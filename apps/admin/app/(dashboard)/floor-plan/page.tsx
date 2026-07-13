'use client';

import { useState, useEffect } from 'react';
import { FloorPlanEditor } from '@/components/FloorPlan/FloorPlanEditor';
import { Plus, ChevronDown } from 'lucide-react';

interface Floor {
    id: string;
    name: string;
    display_order: number;
    is_active: boolean;
    background_image_url: string | null;
}

export default function FloorPlanPage() {
    const [floors, setFloors] = useState<Floor[]>([]);
    const [selectedFloorId, setSelectedFloorId] = useState<string | null>(null);
    const [tables, setTables] = useState([]);
    const [elements, setElements] = useState([]);
    const [loading, setLoading] = useState(true);
    
    useEffect(() => {
        fetchFloors();
    }, []);
    
    useEffect(() => {
        if (selectedFloorId) {
            fetchTables(selectedFloorId);
            fetchElements(selectedFloorId);
        }
    }, [selectedFloorId]);
    
    const fetchFloors = async () => {
        try {
            const response = await fetch('/api/floor-plan/floors');
            if (response.ok) {
                const data = await response.json();
                setFloors(data);
                if (data.length > 0 && !selectedFloorId) {
                    setSelectedFloorId(data[0].id);
                }
            }
        } catch (error) {
            console.error("Failed to fetch floors", error);
        } finally {
            setLoading(false);
        }
    };
    
    const fetchTables = async (floorId: string) => {
        try {
            const response = await fetch(`/api/floor-plan/tables/${floorId}`);
            if (response.ok) {
                const data = await response.json();
                setTables(data);
            }
        } catch (error) {
            console.error("Failed to fetch tables", error);
        }
    };
    
    const fetchElements = async (floorId: string) => {
        try {
            const response = await fetch(`/api/floor-plan/elements/${floorId}`);
            if (response.ok) {
                const data = await response.json();
                setElements(data);
            }
        } catch (error) {
            console.error("Failed to fetch elements", error);
        }
    };
    
    const addNewFloor = async () => {
        const name = prompt('Enter floor name:', 'New Floor');
        if (!name) return;
        
        try {
            const response = await fetch('/api/floor-plan/floors', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: name,
                    display_order: floors.length
                })
            });
            if (response.ok) {
                fetchFloors();
            }
        } catch (error) {
            console.error("Failed to add floor", error);
        }
    };
    
    if (loading) {
        return <div className="p-8 text-center">Loading floor plan...</div>;
    }
    
    return (
        <div className="h-screen flex flex-col">
            {/* Header */}
            <div className="bg-white border-b px-6 py-4 flex justify-between items-center">
                <div>
                    <h1 className="text-2xl font-bold">Floor Plan Designer</h1>
                    <p className="text-gray-500 text-sm">Drag tables to arrange your restaurant layout</p>
                </div>
                
                <div className="flex items-center gap-4">
                    <div className="relative">
                        <select
                            value={selectedFloorId || ''}
                            onChange={(e) => setSelectedFloorId(e.target.value)}
                            className="appearance-none bg-gray-100 border rounded-lg px-4 py-2 pr-8"
                        >
                            {floors.map(floor => (
                                <option key={floor.id} value={floor.id}>
                                    {floor.name}
                                </option>
                            ))}
                        </select>
                        <ChevronDown className="absolute right-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-500 pointer-events-none" />
                    </div>
                    
                    <button
                        onClick={addNewFloor}
                        className="flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700"
                    >
                        <Plus className="w-4 h-4" /> Add Floor
                    </button>
                </div>
            </div>
            
            {/* Floor Plan Editor */}
            {selectedFloorId && (
                <FloorPlanEditor
                    key={selectedFloorId}
                    floorId={selectedFloorId}
                    floorName={floors.find(f => f.id === selectedFloorId)?.name || ''}
                    tables={tables}
                    elements={elements}
                    backgroundImage={floors.find(f => f.id === selectedFloorId)?.background_image_url || undefined}
                    onSave={() => {
                        fetchTables(selectedFloorId);
                        fetchElements(selectedFloorId);
                    }}
                />
            )}
        </div>
    );
}
