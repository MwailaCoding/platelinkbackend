// apps/admin/components/Menu/QuickMenuSetup.tsx
'use client';

import React, { useState } from 'react';
import { X, Trash2, Plus, Loader2 } from 'lucide-react';

interface QuickMenuItem {
  id: string;
  name: string;
  price: number;
  category: string;
  description?: string;
  preparation_time?: number;
}

interface QuickMenuSetupProps {
  onComplete: () => void;
  onSkip: () => void;
}

export default function QuickMenuSetup({ onComplete, onSkip }: QuickMenuSetupProps) {
  const [name, setName] = useState('');
  const [price, setPrice] = useState('');
  const [category, setCategory] = useState('Main Course');
  const [description, setDescription] = useState('');
  const [preparationTime, setPreparationTime] = useState('15');
  
  const [addedItems, setAddedItems] = useState<QuickMenuItem[]>([]);
  const [isAdding, setIsAdding] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Helper to add item via POST api
  const saveItemToDatabase = async (): Promise<QuickMenuItem> => {
    const parsedPrice = parseFloat(price);
    if (!name.trim()) {
      throw new Error('Item Name is required');
    }
    if (isNaN(parsedPrice) || parsedPrice <= 0) {
      throw new Error('A valid positive Price is required');
    }

    const payload = {
      name: name.trim(),
      price: parsedPrice,
      category,
      description: description.trim() || undefined,
      preparation_time: parseInt(preparationTime, 10) || 15
    };

    const res = await fetch('/api/menu/items', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.message || 'Failed to add menu item');
    }

    const newItemData = await res.json();
    return {
      id: newItemData.id || `menu_item_${Date.now()}`,
      name: payload.name,
      price: payload.price,
      category: payload.category,
      description: payload.description,
      preparation_time: payload.preparation_time
    };
  };

  const handleAddItemOnly = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsAdding(true);
    try {
      const newItem = await saveItemToDatabase();
      setAddedItems(prev => [...prev, newItem]);
      
      // Clear form for next item
      setName('');
      setPrice('');
      setDescription('');
      setPreparationTime('15');
    } catch (err: any) {
      setError(err.message || 'An error occurred while saving the item');
    } finally {
      setIsAdding(false);
    }
  };

  const handleSaveAndContinue = async () => {
    setError(null);
    
    // Scenario 1: User has input text in form. We should try to save it first.
    if (name.trim() || price.trim()) {
      setIsAdding(true);
      try {
        const newItem = await saveItemToDatabase();
        // Item added successfully, now we can complete onboarding menu step
        onComplete();
      } catch (err: any) {
        setError(err.message || 'An error occurred while saving the item');
        setIsAdding(false);
      }
    } 
    // Scenario 2: Form is empty, check if we already added items during this session
    else if (addedItems.length > 0) {
      onComplete();
    } 
    // Scenario 3: Form is empty and no items added yet
    else {
      setError('Add at least 1 item to complete this step');
    }
  };

  const handleDeleteItem = (itemId: string) => {
    setAddedItems(prev => prev.filter(item => item.id !== itemId));
  };

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      {/* MODAL CONTENT */}
      <div className="bg-white rounded-xl max-w-md w-full p-6 shadow-2xl relative flex flex-col max-h-[90vh]">
        {/* CLOSE BUTTON */}
        <button 
          onClick={onSkip}
          className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 transition"
        >
          <X className="w-5 h-5" />
        </button>

        {/* HEADER */}
        <div className="mb-4">
          <h3 className="text-lg font-bold text-gray-900">Quick Menu Setup</h3>
          <p className="text-sm text-gray-500 mt-0.5">Add your first item to get started</p>
        </div>

        {/* MAIN BODY SCROLLABLE */}
        <div className="flex-1 overflow-y-auto pr-1 space-y-4">
          
          {/* FORM */}
          <form onSubmit={handleAddItemOnly} className="space-y-3.5">
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">
                Item Name <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g., Grilled Chicken"
                className="rounded-lg border border-gray-300 p-2 w-full text-sm focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 outline-none transition"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">
                  Price (KES) <span className="text-red-500">*</span>
                </label>
                <input
                  type="number"
                  required
                  value={price}
                  onChange={(e) => setPrice(e.target.value)}
                  placeholder="850"
                  className="rounded-lg border border-gray-300 p-2 w-full text-sm focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 outline-none transition"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">
                  Category <span className="text-red-500">*</span>
                </label>
                <select
                  required
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="rounded-lg border border-gray-300 p-2 w-full text-sm bg-white focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 outline-none transition"
                >
                  <option value="Appetizer">Appetizer</option>
                  <option value="Main Course">Main Course</option>
                  <option value="Dessert">Dessert</option>
                  <option value="Beverage">Beverage</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">
                Description (Optional)
              </label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Describe your dish"
                rows={2}
                className="rounded-lg border border-gray-300 p-2 w-full text-sm focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 outline-none transition resize-none"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">
                Preparation Time (minutes)
              </label>
              <input
                type="number"
                value={preparationTime}
                onChange={(e) => setPreparationTime(e.target.value)}
                placeholder="15"
                className="rounded-lg border border-gray-300 p-2 w-full text-sm focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 outline-none transition"
              />
            </div>

            {error && (
              <p className="text-xs text-red-600 font-semibold bg-red-50 p-2 rounded-lg">
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={isAdding}
              className="w-full flex items-center justify-center gap-1.5 px-4 py-2 border border-transparent text-sm font-semibold rounded-lg shadow-sm text-white bg-emerald-600 hover:bg-emerald-700 focus:outline-none transition disabled:opacity-50"
            >
              {isAdding ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Adding...
                </>
              ) : (
                <>
                  <Plus className="w-4 h-4" />
                  Add Item
                </>
              )}
            </button>
          </form>

          {/* PROGRESS INDICATOR */}
          <div className="pt-2 border-t border-gray-100 flex items-center justify-between text-xs text-gray-500">
            <span>Add at least 1 item to complete this step</span>
            <span className="font-semibold text-gray-700">
              {addedItems.length} item{addedItems.length === 1 ? '' : 's'} added
            </span>
          </div>

          {/* ADDED ITEMS LIST */}
          {addedItems.length > 0 && (
            <div className="space-y-1.5">
              <h4 className="text-xs font-bold text-gray-600 uppercase tracking-wide">Added this session</h4>
              <div className="bg-gray-50 border border-gray-100 rounded-lg p-2 max-h-[140px] overflow-y-auto space-y-1">
                {addedItems.map((item) => (
                  <div 
                    key={item.id} 
                    className="flex items-center justify-between bg-white px-2.5 py-1.5 rounded border border-gray-200 text-sm"
                  >
                    <div className="truncate max-w-[70%]">
                      <span className="font-medium text-gray-800">{item.name}</span>
                      <span className="text-xs text-gray-400 ml-1.5">({item.category})</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-gray-900 text-xs shrink-0">
                        KES {item.price.toLocaleString()}
                      </span>
                      <button
                        type="button"
                        onClick={() => handleDeleteItem(item.id)}
                        className="text-gray-400 hover:text-red-600 transition"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

        </div>

        {/* BOTTOM ACTION BUTTONS */}
        <div className="mt-5 pt-3 border-t border-gray-100 grid grid-cols-2 gap-3 shrink-0">
          <button
            type="button"
            onClick={onSkip}
            className="w-full text-center text-sm font-semibold py-2 px-4 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition"
          >
            Skip for now
          </button>
          
          <button
            type="button"
            onClick={handleSaveAndContinue}
            disabled={addedItems.length === 0 && !name.trim()}
            className="w-full text-center text-sm font-semibold py-2 px-4 rounded-lg text-white bg-emerald-600 hover:bg-emerald-700 transition disabled:opacity-50 disabled:bg-gray-300 disabled:cursor-not-allowed"
          >
            Save & Continue
          </button>
        </div>
      </div>
    </div>
  );
}
