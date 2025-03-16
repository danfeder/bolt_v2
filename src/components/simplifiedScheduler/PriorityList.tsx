import React, { useState } from 'react';
import { Priority } from './types';

interface PriorityListProps {
  priorities: Priority[];
  onReorder: (newPriorities: Priority[]) => void;
  disabled?: boolean;
}

/**
 * A drag-and-drop priority list component that allows users to reorder scheduling priorities
 */
export const PriorityList: React.FC<PriorityListProps> = ({
  priorities,
  onReorder,
  disabled = false
}) => {
  const [draggedItem, setDraggedItem] = useState<Priority | null>(null);
  
  // Handle drag start
  const handleDragStart = (e: React.DragEvent<HTMLLIElement>, item: Priority) => {
    setDraggedItem(item);
    // Set transparent drag image
    if (e.dataTransfer.setDragImage) {
      const dragEl = e.currentTarget;
      e.dataTransfer.setDragImage(dragEl, 20, 20);
    }
    // Required for Firefox
    e.dataTransfer.effectAllowed = 'move';
  };
  
  // Handle drag over - needed to allow dropping
  const handleDragOver = (e: React.DragEvent<HTMLLIElement>) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  };
  
  // Handle drop - reorder items
  const handleDrop = (e: React.DragEvent<HTMLLIElement>, targetIndex: number) => {
    e.preventDefault();
    
    if (!draggedItem) return;
    
    const sourceIndex = priorities.findIndex(item => item.id === draggedItem.id);
    if (sourceIndex === targetIndex) return;
    
    // Create new array with reordered items
    const newPriorities = [...priorities];
    newPriorities.splice(sourceIndex, 1);
    newPriorities.splice(targetIndex, 0, draggedItem);
    
    onReorder(newPriorities);
    setDraggedItem(null);
  };
  
  // Handle drag end - reset state
  const handleDragEnd = () => {
    setDraggedItem(null);
  };
  
  return (
    <div className={`rounded-lg border border-gray-200 ${disabled ? 'opacity-60' : ''}`}>
      <ul className="divide-y divide-gray-200">
        {priorities.map((item, index) => (
          <li 
            key={item.id}
            draggable={!disabled}
            onDragStart={(e) => handleDragStart(e, item)}
            onDragOver={handleDragOver}
            onDrop={(e) => handleDrop(e, index)}
            onDragEnd={handleDragEnd}
            className={`
              p-4 flex items-center 
              ${draggedItem?.id === item.id ? 'bg-blue-50' : 'bg-white'} 
              ${!disabled ? 'cursor-grab' : 'cursor-not-allowed'}
              hover:bg-gray-50 transition-colors duration-150
            `}
          >
            <div className="mr-4 text-gray-400">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" className="bi bi-grip-vertical" viewBox="0 0 16 16">
                <path d="M7 2a1 1 0 1 1-2 0 1 1 0 0 1 2 0zm3 0a1 1 0 1 1-2 0 1 1 0 0 1 2 0zM7 5a1 1 0 1 1-2 0 1 1 0 0 1 2 0zm3 0a1 1 0 1 1-2 0 1 1 0 0 1 2 0zM7 8a1 1 0 1 1-2 0 1 1 0 0 1 2 0zm3 0a1 1 0 1 1-2 0 1 1 0 0 1 2 0zM7 11a1 1 0 1 1-2 0 1 1 0 0 1 2 0zm3 0a1 1 0 1 1-2 0 1 1 0 0 1 2 0zM7 14a1 1 0 1 1-2 0 1 1 0 0 1 2 0zm3 0a1 1 0 1 1-2 0 1 1 0 0 1 2 0z"/>
              </svg>
            </div>
            <div>
              <h4 className="font-medium text-gray-800">{item.name}</h4>
              <p className="text-sm text-gray-500">{item.description}</p>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
};
