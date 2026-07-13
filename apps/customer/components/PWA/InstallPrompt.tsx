// apps/customer/components/PWA/InstallPrompt.tsx
"use client";

import React, { useEffect, useState, useRef } from 'react';
import { Smartphone, Download, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export interface InstallPromptProps {
  autoShowDelay?: number; // milliseconds to wait before showing (default: 5000)
  showOnMobileOnly?: boolean; // default: true
  onInstallSuccess?: () => void;
  onInstallDismiss?: () => void;
}

interface BeforeInstallPromptEvent extends Event {
  readonly platforms: string[];
  readonly userChoice: Promise<{
    outcome: 'accepted' | 'dismissed';
    platform: string;
  }>;
  prompt(): Promise<void>;
}

export default function InstallPrompt({
  autoShowDelay = 5000,
  showOnMobileOnly = true,
  onInstallSuccess,
  onInstallDismiss,
}: InstallPromptProps) {
  const [canInstall, setCanInstall] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const [deferredPrompt, setDeferredPrompt] = useState<BeforeInstallPromptEvent | null>(null);
  const [isDismissed, setIsDismissed] = useState(true); // Default to true to prevent Next.js SSR hydration flash
  const [isIos, setIsIos] = useState(false);
  const [showIosInstructions, setShowIosInstructions] = useState(false);

  const installButtonRef = useRef<HTMLButtonElement>(null);
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  // Initialize and check eligibility
  useEffect(() => {
    if (typeof window === 'undefined') return;

    // Detect if app is already running in standalone/installed mode
    const isStandalone = 
      window.matchMedia('(display-mode: standalone)').matches || 
      (window.navigator as any).standalone === true;

    if (isStandalone) {
      return;
    }

    // Detect iOS
    const userAgent = window.navigator.userAgent.toLowerCase();
    const detectIos = /iphone|ipad|ipod/.test(userAgent);
    setIsIos(detectIos);

    // Check persistence dismissal
    const neverShow = localStorage.getItem('platelink_install_dismissed') === 'never';
    const sessionDismissed = sessionStorage.getItem('platelink_install_dismissed_session') === 'true';
    
    setIsDismissed(neverShow || sessionDismissed);

    if (neverShow || sessionDismissed) {
      return;
    }

    // Capture standard PWA installation event
    const handleBeforeInstallPrompt = (e: Event) => {
      e.preventDefault();
      setDeferredPrompt(e as BeforeInstallPromptEvent);
      setCanInstall(true);
    };

    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);

    // Visiblity/engagement delay rules
    const firstVisitTimeStr = localStorage.getItem('platelink_install_first_visit');
    const now = Date.now();

    if (!firstVisitTimeStr) {
      // First visit: save timestamp and do not show banner
      localStorage.setItem('platelink_install_first_visit', now.toString());
      return;
    }

    const firstVisitTime = Number(firstVisitTimeStr);
    const fiveMinutes = 5 * 60 * 1000;

    // Show only on second visit (> 5 minutes later)
    if (now - firstVisitTime < fiveMinutes) {
      return;
    }

    // Support iOS Safari manual installation or standard beforeinstallprompt
    const shouldShowPrompt = detectIos || ('beforeinstallprompt' in window) || canInstall;

    if (!shouldShowPrompt) {
      return;
    }

    // Mobile check
    if (showOnMobileOnly) {
      const isMobile = /android|webos|iphone|ipad|ipod|blackberry|iemobile|opera mini/i.test(userAgent);
      if (!isMobile) return;
    }

    // Trigger auto show delay
    const timer = setTimeout(() => {
      setIsOpen(true);
      // Auto-focus install button for accessibility focus trap entry
      setTimeout(() => {
        installButtonRef.current?.focus();
      }, 300);
    }, autoShowDelay);

    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
      clearTimeout(timer);
    };
  }, [autoShowDelay, showOnMobileOnly, canInstall]);

  // Handle keyboard accessibility (Escape key to close)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        handleDismissLater();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen]);

  const handleInstall = async () => {
    if (isIos) {
      // iOS doesn't support programmatic PWA install, show instructions
      setShowIosInstructions(true);
      return;
    }

    if (!deferredPrompt) {
      // Native fallback if prompt event not fired but client triggers it
      alert('To install, please use your browser menu options (e.g. "Add to Home screen").');
      return;
    }

    try {
      // Trigger native browser install prompt
      await deferredPrompt.prompt();
      
      // Wait for the user response
      const choiceResult = await deferredPrompt.userChoice;
      
      if (choiceResult.outcome === 'accepted') {
        localStorage.setItem('platelink_install_dismissed', 'never');
        setIsDismissed(true);
        setIsOpen(false);
        if (onInstallSuccess) onInstallSuccess();
      } else {
        // Declined, let them retry in next sessions
        handleDismissLater();
      }
    } catch (err) {
      console.error('PWA Installation error:', err);
    } finally {
      setDeferredPrompt(null);
    }
  };

  const handleDismissLater = () => {
    // Dismiss for current session only
    sessionStorage.setItem('platelink_install_dismissed_session', 'true');
    setIsDismissed(true);
    setIsOpen(false);
    if (onInstallDismiss) onInstallDismiss();
  };

  const handleDismissPermanently = () => {
    // Permanent dismissal
    localStorage.setItem('platelink_install_dismissed', 'never');
    setIsDismissed(true);
    setIsOpen(false);
    if (onInstallDismiss) onInstallDismiss();
  };

  if (isDismissed || !isOpen) {
    return null;
  }

  return (
    <>
      <AnimatePresence>
        <motion.div
          role="dialog"
          aria-label="Install PlateLink Africa Application"
          aria-modal="true"
          initial={{ y: 150, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          exit={{ y: 150, opacity: 0 }}
          transition={{ type: 'spring', damping: 25, stiffness: 220 }}
          className="fixed bottom-0 left-0 right-0 z-50 p-4 md:p-6"
        >
          <div className="mx-auto max-w-lg overflow-hidden rounded-[2rem] border border-gray-100 bg-white/95 p-6 shadow-[0_20px_50px_rgba(0,0,0,0.15)] backdrop-blur-xl md:rounded-[2.5rem]">
            {/* Header / Info Section */}
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-4">
                <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-emerald-50 text-emerald-600 shadow-sm border border-emerald-100/50">
                  {isIos ? <Smartphone className="h-6 w-6" /> : <Download className="h-6 w-6" />}
                </div>
                <div>
                  <h3 className="text-base font-black tracking-tight text-slate-900">
                    Install PlateLink App
                  </h3>
                  <p className="mt-1 text-xs font-semibold leading-relaxed text-slate-500">
                    Get faster ordering, offline menu caching, and push status notifications.
                  </p>
                </div>
              </div>
              <button
                ref={closeButtonRef}
                onClick={handleDismissLater}
                aria-label="Close installation offer"
                className="rounded-full p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600 transition-colors"
              >
                <X className="h-4.5 w-4.5" />
              </button>
            </div>

            {/* Action Buttons */}
            <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <button
                onClick={handleDismissPermanently}
                className="text-center text-xs font-bold text-slate-400 hover:text-slate-600 transition-colors cursor-pointer sm:order-first"
              >
                Never show again
              </button>
              
              <div className="flex items-center gap-3 sm:justify-end shrink-0">
                <button
                  onClick={handleDismissLater}
                  className="flex-1 rounded-2xl border border-slate-200 bg-white px-5 py-3 text-xs font-black uppercase tracking-wider text-slate-600 hover:bg-slate-50 active:scale-98 transition-all duration-150 sm:flex-none sm:px-6"
                >
                  Later
                </button>
                <button
                  ref={installButtonRef}
                  onClick={handleInstall}
                  className="flex-1 rounded-2xl bg-emerald-600 px-5 py-3 text-xs font-black uppercase tracking-wider text-white shadow-lg shadow-emerald-600/20 hover:bg-emerald-700 active:scale-98 transition-all duration-150 sm:flex-none sm:px-6"
                >
                  Install
                </button>
              </div>
            </div>
          </div>
        </motion.div>
      </AnimatePresence>

      {/* iOS Instructions Overlay */}
      <AnimatePresence>
        {showIosInstructions && (
          <div className="fixed inset-0 z-55 flex items-center justify-center p-4">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setShowIosInstructions(false)}
              className="absolute inset-0 bg-slate-900/60 backdrop-blur-sm"
            />
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="relative w-full max-w-sm rounded-[2.5rem] bg-white p-8 shadow-2xl border border-slate-100"
            >
              <div className="text-center">
                <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-50 text-emerald-600 mb-4">
                  <Smartphone className="h-7 w-7" />
                </div>
                <h3 className="text-lg font-black text-slate-900">
                  Install on iOS
                </h3>
                <p className="mt-3 text-xs font-semibold leading-relaxed text-slate-500">
                  Safari doesn't support instant install. Follow these quick steps to add PlateLink to your home screen:
                </p>

                <div className="mt-6 space-y-4 text-left text-xs font-bold text-slate-700">
                  <div className="flex items-center gap-3">
                    <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-slate-100 text-[10px]">1</span>
                    <span>Tap the <span className="text-emerald-600">Share</span> button in your Safari navigation bar.</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-slate-100 text-[10px]">2</span>
                    <span>Scroll down and select <span className="text-emerald-600">"Add to Home Screen"</span>.</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-slate-100 text-[10px]">3</span>
                    <span>Confirm by clicking <span className="text-emerald-600">Add</span> in the top right corner.</span>
                  </div>
                </div>

                <button
                  onClick={() => setShowIosInstructions(false)}
                  className="mt-8 w-full rounded-2xl bg-slate-900 py-3 text-xs font-black uppercase tracking-wider text-white hover:bg-slate-800 transition-colors"
                >
                  Got it
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </>
  );
}
