'use client';

import { useState, useEffect, useRef } from 'react';

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

interface Floor {
    id: string;
    name: string;
}

export default function MobileFloorPlanPage() {
    const [floors, setFloors] = useState<Floor[]>([]);
    const [currentFloor, setCurrentFloor] = useState(0);
    const [tables, setTables] = useState<Table[]>([]);
    const [selectedTable, setSelectedTable] = useState<Table | null>(null);
    const touchStartRef = useRef<number | null>(null);
    
    useEffect(() => {
        fetchFloors();
    }, []);
    
    useEffect(() => {
        if (floors[currentFloor]) {
            fetchTables(floors[currentFloor].id);
        }
    }, [currentFloor, floors]);
    
    const fetchFloors = async () => {
        try {
            const response = await fetch('/api/floor-plan/floors');
            if (response.ok) {
                const data = await response.json();
                setFloors(data);
            }
        } catch (error) {
            console.error("Failed to fetch floors", error);
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
    
    const handleSwipe = (direction: 'left' | 'right') => {
        if (direction === 'left' && currentFloor < floors.length - 1) {
            setCurrentFloor(currentFloor + 1);
        } else if (direction === 'right' && currentFloor > 0) {
            setCurrentFloor(currentFloor - 1);
        }
    };
    
    const handleTouchStart = (e: React.TouchEvent) => {
        touchStartRef.current = e.touches[0].clientX;
    };
    
    const handleTouchEnd = (e: React.TouchEvent) => {
        if (!touchStartRef.current) return;
        const endX = e.changedTouches[0].clientX;
        const diff = touchStartRef.current - endX;
        
        if (Math.abs(diff) > 50) {
            handleSwipe(diff > 0 ? 'left' : 'right');
        }
        touchStartRef.current = null;
    };
    
    const getStatusColor = (status: string) => {
        switch (status) {
            case 'available': return 'bg-green-100 border-green-500';
            case 'occupied': return 'bg-yellow-100 border-yellow-500';
            case 'ordering': return 'bg-orange-100 border-orange-500';
            case 'ordered': return 'bg-blue-100 border-blue-500';
            case 'ready': return 'bg-purple-100 border-purple-500';
            case 'eating': return 'bg-amber-100 border-amber-500';
            case 'bill_requested': return 'bg-pink-100 border-pink-500';
            default: return 'bg-gray-100 border-gray-300';
        }
    };
    
    return (
        <div className="min-h-screen bg-gray-100">
            {/* Floor Selector */}
            <div className="bg-white border-b px-4 py-3">
                <div className="flex items-center justify-between">
                    <button
                        onClick={() => handleSwipe('right')}
                        disabled={currentFloor === 0}
                        className="p-2 disabled:opacity-30"
                    >
                        ←
                    </button>
                    <div className="text-center">
                        <h2 className="font-bold text-lg">{floors[currentFloor]?.name || 'Loading...'}</h2>
                        <p className="text-xs text-gray-500">Swipe to change floor</p>
                    </div>
                    <button
                        onClick={() => handleSwipe('left')}
                        disabled={currentFloor === floors.length - 1}
                        className="p-2 disabled:opacity-30"
                    >
                        →
                    </button>
                </div>
            </div>
            
            {/* Floor Plan Canvas */}
            <div
                className="relative p-4"
                onTouchStart={handleTouchStart}
                onTouchEnd={handleTouchEnd}
            >
                <div className="relative bg-white rounded-xl shadow-lg p-4 min-h-[500px]">
                    {/* Background grid */}
                    <div className="absolute inset-0 opacity-10 pointer-events-none"
                        style={{
                            backgroundImage: `
                                linear-gradient(to right, #000 1px, transparent 1px),
                                linear-gradient(to bottom, #000 1px, transparent 1px)
                            `,
                            backgroundSize: '20px 20px'
                        }}
                    />
                    
                    {/* Tables Grid */}
                    <div className="relative z-10 grid grid-cols-2 gap-3">
                        {tables.map(table => (
                            <div
                                key={table.id}
                                onClick={() => setSelectedTable(table)}
                                className={`p-4 rounded-xl border-2 text-center ${getStatusColor(table.status)}`}
                            >
                                <div className="font-bold text-xl">Table {table.table_number}</div>
                                <div className="text-sm">{table.capacity} seats</div>
                                <div className="text-xs capitalize mt-1">{table.status}</div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
            
            {/* Table Details Modal */}
            {selectedTable && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
                    <div className="bg-white rounded-xl max-w-sm w-full p-6">
                        <h3 className="text-xl font-bold mb-2">Table {selectedTable.table_number}</h3>
                        <p className="text-gray-500 mb-4">Capacity: {selectedTable.capacity} seats</p>
                        
                        <div className="mb-4">
                            <label className="block text-sm font-medium mb-1">Status</label>
                            <select
                                value={selectedTable.status}
                                className="w-full border rounded-lg p-2"
                                onChange={async (e) => {
                                    try {
                                        await fetch(`/api/tables/${selectedTable.id}/status`, {
                                            method: 'PUT',
                                            headers: { 'Content-Type': 'application/json' },
                                            body: JSON.stringify({ status: e.target.value })
                                        });
                                        setSelectedTable(null);
                                        fetchTables(floors[currentFloor]?.id);
                                    } catch (error) {
                                        console.error("Failed to update status", error);
                                    }
                                }}
                            >
                                <option value="available">Available</option>
                                <option value="occupied">Occupied</option>
                                <option value="cleaning">Cleaning</option>
                                <option value="reserved">Reserved</option>
                            </select>
                        </div>
                        
                        <button
                            onClick={() => setSelectedTable(null)}
                            className="w-full py-2 bg-gray-200 rounded-lg"
                        >
                            Close
                        </button>
                    </div>
                </div>
            )}
            
            {/* Legend */}
            <div className="fixed bottom-0 left-0 right-0 bg-white border-t p-3">
                <div className="flex justify-around text-xs">
                    <div className="flex items-center gap-1">
                        <div className="w-3 h-3 bg-green-500 rounded"></div>
                        <span>Available</span>
                    </div>
                    <div className="flex items-center gap-1">
                        <div className="w-3 h-3 bg-yellow-500 rounded"></div>
                        <span>Occupied</span>
                    </div>
                    <div className="flex items-center gap-1">
                        <div className="w-3 h-3 bg-blue-500 rounded"></div>
                        <span>Ordered</span>
                    </div>
                    <div className="flex items-center gap-1">
                        <div className="w-3 h-3 bg-purple-500 rounded"></div>
                        <span>Ready</span>
                    </div>
                </div>
            </div>
        </div>
    );
}
