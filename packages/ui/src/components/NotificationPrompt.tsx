// packages/ui/src/components/NotificationPrompt.tsx
import React, { useState, useEffect } from 'react';
import { Bell } from 'lucide-react';

export interface NotificationPromptProps {
  onPermissionGranted?: () => void;
  onPermissionDenied?: () => void;
  onDismiss?: () => void;
  autoShowDelay?: number;
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left';
}

export const NotificationPrompt: React.FC<NotificationPromptProps> = ({
  onPermissionGranted,
  onPermissionDenied,
  onDismiss,
  autoShowDelay = 3000,
  position = 'bottom-right',
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const [isSupported, setIsSupported] = useState(true);

  useEffect(() => {
    if (typeof window === 'undefined' || !('Notification' in window)) {
      setIsSupported(false);
      return;
    }

    if (Notification.permission === 'granted') {
      onPermissionGranted?.();
      return;
    }

    if (Notification.permission === 'denied') {
      onPermissionDenied?.();
      return;
    }

    const isDismissed = localStorage.getItem('platelink_notification_prompt_dismissed');
    if (isDismissed) {
      return;
    }

    const timer = setTimeout(() => {
      setIsVisible(true);
    }, autoShowDelay);

    return () => clearTimeout(timer);
  }, [autoShowDelay, onPermissionGranted, onPermissionDenied]);

  const handleAllow = async () => {
    try {
      const permission = await Notification.requestPermission();
      if (permission === 'granted') {
        onPermissionGranted?.();
      } else if (permission === 'denied') {
        onPermissionDenied?.();
      }
    } catch (error) {
      console.error('Error requesting notification permission:', error);
    }
    setIsVisible(false);
  };

  const handleDismiss = () => {
    localStorage.setItem('platelink_notification_prompt_dismissed', 'true');
    setIsVisible(false);
    onDismiss?.();
  };

  if (!isSupported || !isVisible) {
    return null;
  }

  const positionClasses = {
    'top-right': 'top-4 right-4',
    'top-left': 'top-4 left-4',
    'bottom-right': 'bottom-4 right-4',
    'bottom-left': 'bottom-4 left-4',
  };

  return (
    <div
      className={`fixed z-50 max-w-sm w-full bg-white rounded-xl shadow-lg border border-gray-100 p-4 transition-all transform animate-in slide-in-from-${
        position.includes('bottom') ? 'bottom' : 'top'
      }-10 fade-in duration-300 ${positionClasses[position]}`}
    >
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 bg-blue-50 p-2 rounded-lg">
          <Bell className="w-6 h-6 text-blue-600" />
        </div>
        <div className="flex-1">
          <h3 className="text-gray-900 font-semibold mb-1">Get Real-Time Updates</h3>
          <p className="text-gray-600 text-sm mb-4 leading-relaxed">
            Enable notifications to receive real-time updates about new orders, ready pickups, and customer calls.
          </p>
          <div className="flex items-center gap-3">
            <button
              onClick={handleAllow}
              className="flex-1 bg-emerald-500 hover:bg-emerald-600 text-white font-medium py-2 px-4 rounded-lg transition-colors text-sm"
            >
              Allow
            </button>
            <button
              onClick={handleDismiss}
              className="flex-1 bg-white hover:bg-gray-50 text-gray-700 font-medium py-2 px-4 rounded-lg border border-gray-300 transition-colors text-sm"
            >
              Later
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
