// packages/ui/src/components/ConnectionStatus.tsx
import React from 'react';

export interface ConnectionStatusProps {
  isConnected: boolean;
  isReconnecting: boolean;
  error: string | null;
  showLabel?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

export const ConnectionStatus: React.FC<ConnectionStatusProps> = ({
  isConnected,
  isReconnecting,
  error,
  showLabel = true,
  size = 'md',
}) => {
  let state: 'connected' | 'connecting' | 'reconnecting' | 'disconnected' | 'error' = 'disconnected';

  if (error !== null) {
    state = 'error';
  } else if (isReconnecting) {
    state = 'reconnecting';
  } else if (isConnected) {
    state = 'connected';
  } else if (!isConnected && isReconnecting) {
    state = 'connecting';
  } else if (!isConnected && !isReconnecting) {
    state = 'disconnected';
  }

  // Refine state logic based on prompt exact instructions:
  if (error !== null) {
    state = 'error';
  } else if (isConnected && !isReconnecting) {
    state = 'connected';
  } else if (!isConnected && isReconnecting) {
    state = 'connecting';
  } else if (isReconnecting && error === null) {
    state = 'reconnecting';
  } else {
    state = 'disconnected';
  }

  const sizeClasses = {
    sm: { dot: 'w-2 h-2', text: 'text-xs' },
    md: { dot: 'w-3 h-3', text: 'text-sm' },
    lg: { dot: 'w-4 h-4', text: 'text-base' },
  };

  const stateConfig = {
    connected: {
      color: 'bg-green-500',
      textColor: 'text-green-500',
      label: 'Live',
      animation: 'animate-ping',
    },
    connecting: {
      color: 'bg-yellow-500',
      textColor: 'text-yellow-500',
      label: 'Connecting...',
      animation: 'slow-pulse',
    },
    reconnecting: {
      color: 'bg-orange-500',
      textColor: 'text-orange-500',
      label: 'Reconnecting...',
      animation: 'fast-pulse',
    },
    disconnected: {
      color: 'bg-red-500',
      textColor: 'text-red-500',
      label: 'Offline',
      animation: '',
    },
    error: {
      color: 'bg-red-500',
      textColor: 'text-red-500',
      label: error || 'Error',
      animation: '',
    },
  };

  const currentConfig = stateConfig[state];

  return (
    <div
      className="flex flex-row items-center gap-2"
      role="status"
      aria-label={`Connection status: ${currentConfig.label}`}
    >
      <style>{`
        @keyframes fast-pulse {
          0%, 100% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.5; transform: scale(1.2); }
        }
        @keyframes slow-pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.7; }
        }
        .fast-pulse {
          animation: fast-pulse 0.5s ease-in-out infinite;
        }
        .slow-pulse {
          animation: slow-pulse 2s ease-in-out infinite;
        }
      `}</style>
      <div className="relative flex items-center justify-center">
        {currentConfig.animation && (
          <div
            className={`absolute rounded-full ${currentConfig.color} ${sizeClasses[size].dot} ${currentConfig.animation} opacity-75`}
          />
        )}
        <div
          className={`relative rounded-full ${currentConfig.color} ${sizeClasses[size].dot}`}
        />
      </div>
      {showLabel && (
        <span
          className={`${currentConfig.textColor} ${sizeClasses[size].text} font-medium ${
            state === 'error' ? 'truncate max-w-[200px]' : ''
          }`}
          title={state === 'error' ? (error as string) : undefined}
        >
          {currentConfig.label}
        </span>
      )}
    </div>
  );
};
