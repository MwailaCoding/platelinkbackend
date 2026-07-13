'use client';

import { useState, useRef, useCallback, useEffect } from 'react';
import {
    DndContext,
    closestCenter,
    KeyboardSensor,
    PointerSensor,
    useSensor,
    useSensors,
    DragEndEvent,
    DragOverlay
} from '@dnd-kit/core';
import {
    arrayMove,
    SortableContext,
    rectSortingStrategy,
    useSortable
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { Grid, Ruler, Printer, Copy, Download, Trash2, Plus } from 'lucide-react';

interface Table {
    id: string;
    table_number: number;
    capacity: number;
    status: string;
    pos_x: number;
    pos_y: number;
    shape: string;
    width: number;
    height: number;
}

interface FloorElement {
    id: string;
    type: 'wall' | 'door' | 'window' | 'bar' | 'host_stand';
    data: {
        x1: number;
        y1: number;
        x2: number;
        y2: number;
        x?: number;
        y?: number;
        width?: number;
        height?: number;
        thickness?: number;
    };
}

interface FloorPlanEditorProps {
    floorId: string;
    floorName: string;
    tables: Table[];
    elements: FloorElement[];
    backgroundImage?: string;
    onSave: () => void;
}

export function FloorPlanEditor({
    floorId,
    floorName,
    tables: initialTables,
    elements: initialElements,
    backgroundImage,
    onSave
}: FloorPlanEditorProps) {
    const [tables, setTables] = useState(initialTables);
    const [elements, setElements] = useState(initialElements);
    const [selectedTool, setSelectedTool] = useState<'select' | 'table' | 'wall' | 'door' | 'window'>('select');
    const [gridSize, setGridSize] = useState(20);
    const [snapEnabled, setSnapEnabled] = useState(true);
    const [showGrid, setShowGrid] = useState(true);
    const [zoom, setZoom] = useState(100);
    const [isDrawing, setIsDrawing] = useState(false);
    const [currentWall, setCurrentWall] = useState<{startX: number, startY: number} | null>(null);
    const canvasRef = useRef<HTMLDivElement>(null);
    const containerRef = useRef<HTMLDivElement>(null);

    // Load settings
    useEffect(() => {
        fetchSettings();
    }, []);

    const fetchSettings = async () => {
        try {
            const response = await fetch('/api/settings/floor-plan');
            if (response.ok) {
                const data = await response.json();
                setGridSize(data.grid_size);
                setSnapEnabled(data.snap_enabled);
                setShowGrid(data.show_grid);
            }
        } catch (error) {
            console.error("Failed to fetch settings", error);
        }
    };

    const snapToGrid = useCallback((value: number) => {
        if (!snapEnabled) return value;
        return Math.round(value / gridSize) * gridSize;
    }, [snapEnabled, gridSize]);

    const handleTableDragEnd = async (event: DragEndEvent) => {
        const { active, delta } = event;
        const tableId = active.id;
        const table = tables.find(t => t.id === tableId);
        
        if (table) {
            const newX = snapToGrid(table.pos_x + delta.x);
            const newY = snapToGrid(table.pos_y + delta.y);
            
            const updatedTables = tables.map(t =>
                t.id === tableId ? { ...t, pos_x: newX, pos_y: newY } : t
            );
            setTables(updatedTables);
            
            // Auto-save position
            await saveTablePositions(updatedTables);
        }
    };

    const saveTablePositions = async (updatedTables: Table[]) => {
        try {
            await fetch('/api/floor-plan/tables/positions', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    floor_id: floorId,
                    tables: updatedTables.map(t => ({
                        id: t.id,
                        x: t.pos_x,
                        y: t.pos_y
                    }))
                })
            });
        } catch (error) {
            console.error("Failed to save table positions", error);
        }
    };

    const handleCanvasClick = (e: React.MouseEvent) => {
        if (selectedTool === 'table') {
            addNewTable(e);
        } else if (selectedTool === 'wall' && isDrawing) {
            finishWall(e);
        } else if (selectedTool === 'door' || selectedTool === 'window') {
            addElement(e, selectedTool);
        }
    };

    const addNewTable = async (e: React.MouseEvent) => {
        const rect = canvasRef.current?.getBoundingClientRect();
        if (!rect) return;
        
        const x = snapToGrid(e.clientX - rect.left);
        const y = snapToGrid(e.clientY - rect.top);
        
        const newTable = {
            table_number: tables.length + 1,
            capacity: 4,
            shape: 'square',
            pos_x: x,
            pos_y: y,
            width: 80,
            height: 80,
            floor_id: floorId
        };
        
        try {
            const response = await fetch('/api/tables', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(newTable)
            });
            
            if (response.ok) {
                const data = await response.json();
                setTables([...tables, data]);
                onSave();
            }
        } catch (error) {
            console.error("Failed to add table", error);
        }
    };

    const addElement = async (e: React.MouseEvent, type: 'door' | 'window') => {
        const rect = canvasRef.current?.getBoundingClientRect();
        if (!rect) return;
        
        const x = snapToGrid(e.clientX - rect.left);
        const y = snapToGrid(e.clientY - rect.top);
        
        const newElement = {
            floor_id: floorId,
            element_type: type,
            element_data: {
                x: x,
                y: y,
                width: type === 'door' ? 40 : 60,
                height: type === 'door' ? 10 : 15
            }
        };
        
        try {
            const response = await fetch('/api/floor-plan/elements', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(newElement)
            });
            
            if (response.ok) {
                const data = await response.json();
                setElements([...elements, data.element]);
                onSave();
            }
        } catch (error) {
            console.error("Failed to add element", error);
        }
    };

    const startWall = (e: React.MouseEvent) => {
        const rect = canvasRef.current?.getBoundingClientRect();
        if (!rect) return;
        
        const x = snapToGrid(e.clientX - rect.left);
        const y = snapToGrid(e.clientY - rect.top);
        setCurrentWall({ startX: x, startY: y });
        setIsDrawing(true);
    };

    const finishWall = async (e: React.MouseEvent) => {
        const rect = canvasRef.current?.getBoundingClientRect();
        if (!rect || !currentWall) return;
        
        const endX = snapToGrid(e.clientX - rect.left);
        const endY = snapToGrid(e.clientY - rect.top);
        
        const newWall = {
            floor_id: floorId,
            element_type: 'wall',
            element_data: {
                x1: currentWall.startX,
                y1: currentWall.startY,
                x2: endX,
                y2: endY,
                thickness: 20
            }
        };
        
        try {
            const response = await fetch('/api/floor-plan/elements', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(newWall)
            });
            
            if (response.ok) {
                const data = await response.json();
                setElements([...elements, data.element]);
                onSave();
            }
        } catch (error) {
            console.error("Failed to add wall", error);
        } finally {
            setIsDrawing(false);
            setCurrentWall(null);
        }
    };

    const handlePrint = async () => {
        try {
            const response = await fetch(`/api/floor-plan/print/${floorId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    include_table_numbers: true,
                    include_capacities: true,
                    include_legend: true
                })
            });
            
            if (response.ok) {
                const blob = await response.blob();
                const url = URL.createObjectURL(blob);
                window.open(url, '_blank');
            }
        } catch (error) {
            console.error("Failed to print", error);
        }
    };

    const handleCopyFloor = async () => {
        const newName = prompt('Enter name for new floor:', `${floorName} (Copy)`);
        if (!newName) return;
        
        try {
            const response = await fetch(`/api/floor-plan/floors/${floorId}/copy`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    new_name: newName,
                    display_order: tables.length
                })
            });
            
            if (response.ok) {
                alert('Floor copied successfully!');
                onSave();
            }
        } catch (error) {
            console.error("Failed to copy floor", error);
        }
    };

    const sensors = useSensors(
        useSensor(PointerSensor),
        useSensor(KeyboardSensor)
    );

    return (
        <div className="flex flex-col h-full">
            {/* Toolbar */}
            <div className="bg-white border-b p-2 flex items-center gap-2 flex-wrap">
                <div className="flex bg-gray-100 rounded-lg p-1">
                    <button
                        onClick={() => setSelectedTool('select')}
                        className={`px-3 py-1.5 rounded-md text-sm ${selectedTool === 'select' ? 'bg-emerald-600 text-white' : 'hover:bg-gray-200'}`}
                    >
                        Select
                    </button>
                    <button
                        onClick={() => setSelectedTool('table')}
                        className={`px-3 py-1.5 rounded-md text-sm ${selectedTool === 'table' ? 'bg-emerald-600 text-white' : 'hover:bg-gray-200'}`}
                    >
                        + Table
                    </button>
                    <button
                        onClick={() => setSelectedTool('wall')}
                        className={`px-3 py-1.5 rounded-md text-sm ${selectedTool === 'wall' ? 'bg-emerald-600 text-white' : 'hover:bg-gray-200'}`}
                    >
                        █ Wall
                    </button>
                    <button
                        onClick={() => setSelectedTool('door')}
                        className={`px-3 py-1.5 rounded-md text-sm ${selectedTool === 'door' ? 'bg-emerald-600 text-white' : 'hover:bg-gray-200'}`}
                    >
                        🚪 Door
                    </button>
                    <button
                        onClick={() => setSelectedTool('window')}
                        className={`px-3 py-1.5 rounded-md text-sm ${selectedTool === 'window' ? 'bg-emerald-600 text-white' : 'hover:bg-gray-200'}`}
                    >
                        Window
                    </button>
                </div>
                
                <div className="w-px h-8 bg-gray-300"></div>
                
                <div className="flex items-center gap-2">
                    <button
                        onClick={() => setSnapEnabled(!snapEnabled)}
                        className={`p-1.5 rounded-md ${snapEnabled ? 'bg-emerald-100 text-emerald-600' : 'hover:bg-gray-100'}`}
                        title="Snap to Grid"
                    >
                        <Grid className="w-4 h-4" />
                    </button>
                    <button
                        onClick={() => setShowGrid(!showGrid)}
                        className={`p-1.5 rounded-md ${showGrid ? 'bg-emerald-100 text-emerald-600' : 'hover:bg-gray-100'}`}
                        title="Show Grid"
                    >
                        <Ruler className="w-4 h-4" />
                    </button>
                    <select
                        value={gridSize}
                        onChange={(e) => setGridSize(parseInt(e.target.value))}
                        className="border rounded-md px-2 py-1 text-sm"
                    >
                        <option value={10}>10px Grid</option>
                        <option value={20}>20px Grid</option>
                        <option value={30}>30px Grid</option>
                        <option value={50}>50px Grid</option>
                    </select>
                </div>
                
                <div className="w-px h-8 bg-gray-300"></div>
                
                <div className="flex items-center gap-2">
                    <button
                        onClick={handlePrint}
                        className="px-3 py-1.5 bg-gray-100 rounded-md text-sm hover:bg-gray-200 flex items-center gap-1"
                    >
                        <Printer className="w-4 h-4" /> Print
                    </button>
                    <button
                        onClick={handleCopyFloor}
                        className="px-3 py-1.5 bg-gray-100 rounded-md text-sm hover:bg-gray-200 flex items-center gap-1"
                    >
                        <Copy className="w-4 h-4" /> Copy Floor
                    </button>
                </div>
                
                <div className="flex-1"></div>
                
                <div className="flex items-center gap-2">
                    <span className="text-sm text-gray-500">Zoom:</span>
                    <select
                        value={zoom}
                        onChange={(e) => setZoom(parseInt(e.target.value))}
                        className="border rounded-md px-2 py-1 text-sm"
                    >
                        <option value={50}>50%</option>
                        <option value={75}>75%</option>
                        <option value={100}>100%</option>
                        <option value={125}>125%</option>
                        <option value={150}>150%</option>
                    </select>
                </div>
            </div>
            
            {/* Canvas */}
            <div
                ref={containerRef}
                className="flex-1 overflow-auto bg-gray-100 p-4"
                style={{ background: '#E5E7EB' }}
            >
                <div
                    ref={canvasRef}
                    className="relative bg-white shadow-lg mx-auto"
                    style={{
                        width: 1200,
                        height: 800,
                        transform: `scale(${zoom / 100})`,
                        transformOrigin: 'top left',
                        backgroundImage: showGrid ? `
                            linear-gradient(to right, #E5E7EB 1px, transparent 1px),
                            linear-gradient(to bottom, #E5E7EB 1px, transparent 1px)
                        ` : 'none',
                        backgroundSize: `${gridSize}px ${gridSize}px`,
                        backgroundPosition: 'center center'
                    }}
                    onClick={handleCanvasClick}
                    onMouseDown={selectedTool === 'wall' && !isDrawing ? startWall : undefined}
                >
                    {/* Background image (blueprint) */}
                    {backgroundImage && (
                        <img
                            src={backgroundImage}
                            alt="Floor plan blueprint"
                            className="absolute inset-0 w-full h-full object-contain opacity-30 pointer-events-none"
                        />
                    )}
                    
                    {/* Walls */}
                    {elements.filter(e => e.type === 'wall').map(wall => (
                        <div
                            key={wall.id}
                            className="absolute bg-gray-800"
                            style={{
                                left: Math.min(wall.data.x1!, wall.data.x2!),
                                top: Math.min(wall.data.y1!, wall.data.y2!),
                                width: Math.max(Math.abs(wall.data.x2! - wall.data.x1!), wall.data.thickness || 20),
                                height: Math.max(Math.abs(wall.data.y2! - wall.data.y1!), wall.data.thickness || 20),
                            }}
                        />
                    ))}
                    
                    {/* Doors */}
                    {elements.filter(e => e.type === 'door').map(door => (
                        <div
                            key={door.id}
                            className="absolute bg-amber-200 border border-amber-600"
                            style={{
                                left: door.data.x,
                                top: door.data.y,
                                width: door.data.width || 40,
                                height: door.data.height || 10
                            }}
                        >
                            <span className="text-xs absolute -top-4 left-0">🚪</span>
                        </div>
                    ))}
                    
                    {/* Windows */}
                    {elements.filter(e => e.type === 'window').map(window => (
                        <div
                            key={window.id}
                            className="absolute bg-blue-100 border border-blue-400"
                            style={{
                                left: window.data.x,
                                top: window.data.y,
                                width: window.data.width || 60,
                                height: window.data.height || 15
                            }}
                        >
                            <span className="text-xs absolute -top-4 left-0">🪟</span>
                        </div>
                    ))}
                    
                    {/* Tables (Draggable) */}
                    <DndContext
                        sensors={sensors}
                        collisionDetection={closestCenter}
                        onDragEnd={handleTableDragEnd}
                    >
                        <SortableContext
                            items={tables.map(t => t.id)}
                            strategy={rectSortingStrategy}
                        >
                            {tables.map(table => (
                                <SortableTable
                                    key={table.id}
                                    table={table}
                                />
                            ))}
                        </SortableContext>
                    </DndContext>
                    
                    {/* Drawing preview for walls */}
                    {isDrawing && currentWall && (
                        <div
                            className="absolute border-2 border-emerald-500 border-dashed"
                            style={{
                                left: currentWall.startX,
                                top: currentWall.startY,
                                right: 0,
                                bottom: 0
                            }}
                        />
                    )}
                </div>
            </div>
        </div>
    );
}

// Sortable Table Component
function SortableTable({ table }: { table: Table }) {
    const {
        attributes,
        listeners,
        setNodeRef,
        transform,
        transition,
        isDragging
    } = useSortable({ id: table.id });
    
    const style = {
        transform: CSS.Transform.toString(transform),
        transition,
        position: 'absolute' as const,
        left: table.pos_x,
        top: table.pos_y,
        width: table.width,
        height: table.height,
        cursor: isDragging ? 'grabbing' : 'grab',
        opacity: isDragging ? 0.5 : 1,
        zIndex: isDragging ? 1000 : 1
    };
    
    const getStatusColor = () => {
        switch (table.status) {
            case 'available': return 'bg-green-100 border-green-500 text-green-800';
            case 'occupied': return 'bg-yellow-100 border-yellow-500 text-yellow-800';
            case 'ordering': return 'bg-orange-100 border-orange-500 text-orange-800';
            case 'ordered': return 'bg-blue-100 border-blue-500 text-blue-800';
            case 'ready': return 'bg-purple-100 border-purple-500 text-purple-800';
            case 'eating': return 'bg-amber-100 border-amber-500 text-amber-800';
            case 'bill_requested': return 'bg-pink-100 border-pink-500 text-pink-800';
            case 'cleaning': return 'bg-gray-100 border-gray-500 text-gray-800';
            default: return 'bg-white border-gray-300';
        }
    };
    
    return (
        <div
            ref={setNodeRef}
            style={style}
            className={`rounded-lg border-2 shadow-sm flex flex-col items-center justify-center ${getStatusColor()}`}
            {...attributes}
            {...listeners}
        >
            <span className="font-bold text-lg">{table.table_number}</span>
            <span className="text-xs">{table.capacity} seats</span>
        </div>
    );
}

function getAngle(wall: { x1?: number; y1?: number; x2?: number; y2?: number }): number {
    if (wall.x1 === undefined || wall.y1 === undefined || wall.x2 === undefined || wall.y2 === undefined) return 0;
    return Math.atan2(wall.y2 - wall.y1, wall.x2 - wall.x1) * 180 / Math.PI;
}
