import React from 'react';
import { motion, AnimatePresence, useReducedMotion } from 'motion/react';
import { X, Bell, CheckCheck, ShieldAlert, Sparkles, ExternalLink } from 'lucide-react';
import { NotificationItem } from '../../types';

interface NotificationDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  notifications: NotificationItem[];
  onMarkAllAsRead: () => void;
}

export const NotificationDrawer: React.FC<NotificationDrawerProps> = ({
  isOpen,
  onClose,
  notifications,
  onMarkAllAsRead,
}) => {
  const shouldReduceMotion = useReducedMotion();

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex justify-end">
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2, ease: [0.4, 0, 0.2, 1] }}
            onClick={onClose}
            className="fixed inset-0 bg-black/60 backdrop-blur-xs cursor-pointer"
          />

          {/* Drawer Panel */}
          <motion.div
            initial={shouldReduceMotion ? { opacity: 0 } : { x: '100%' }}
            animate={shouldReduceMotion ? { opacity: 1 } : { x: 0 }}
            exit={shouldReduceMotion ? { opacity: 0 } : { x: '100%' }}
            transition={
              shouldReduceMotion
                ? { duration: 0.2 }
                : { type: 'spring', stiffness: 350, damping: 30 }
            }
            className="relative z-10 w-full max-w-sm h-full shadow-2xl p-6 flex flex-col border-l transition-colors bg-[#FFFDFA] border-[#E9D6C4] text-[#2E0A12] dark:bg-[#23262F] dark:border-[#333742] dark:text-white"
          >
            {/* Drawer Header */}
            <div className="flex items-center justify-between pb-4 border-b border-[#E9D6C4] dark:border-[#333742]">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-xl flex items-center justify-center bg-[#FBF1E3] text-[#800020] border border-[#E9D6C4] dark:bg-[#181A20] dark:text-[#B6FF2E] dark:border-[#B6FF2E]/30">
                  <Bell size={16} />
                </div>
                <h3 className="font-extrabold text-base text-[#2E0A12] dark:text-white">Notifications</h3>
              </div>
              <button
                onClick={onClose}
                aria-label="Close Notifications"
                className="w-8 h-8 rounded-lg flex items-center justify-center transition-colors bg-[#FBF1E3] hover:bg-[#EFE0D1] text-[#6C3B45] dark:bg-[#181A20] dark:hover:bg-[#2A2E38] dark:text-slate-300 cursor-pointer"
              >
                <X size={16} />
              </button>
            </div>

            {/* Actions Bar */}
            <div className="py-3 flex justify-between items-center text-xs">
              <span className="font-semibold text-[#8A6A72] dark:text-slate-400">
                {notifications.filter(n => !n.read).length} unread
              </span>
              <button
                onClick={onMarkAllAsRead}
                className="font-bold flex items-center gap-1 cursor-pointer transition-colors text-[#800020] hover:text-[#6E1B33] dark:text-[#B6FF2E] dark:hover:text-[#A3E823]"
              >
                <CheckCheck size={14} />
                <span>Mark all read</span>
              </button>
            </div>

            {/* Notification Items List with Staggered Entrance */}
            <div className="flex-1 overflow-y-auto space-y-3 pr-1">
              {notifications.map((item, index) => (
                <motion.div
                  key={item.id}
                  initial={shouldReduceMotion ? { opacity: 0 } : { opacity: 0, y: 10, scale: 0.98 }}
                  animate={shouldReduceMotion ? { opacity: 1 } : { opacity: 1, y: 0, scale: 1 }}
                  transition={{
                    duration: 0.25,
                    delay: Math.min(index * 0.04, 0.3),
                    ease: [0.22, 1, 0.36, 1],
                  }}
                  className={`p-4 rounded-2xl border transition-all ${
                    item.read 
                      ? 'bg-[#FBF1E3]/60 border-[#E9D6C4]/60 opacity-75 dark:bg-[#181A20]/40 dark:border-[#333742]' 
                      : 'bg-[#FBF1E3] border-[#E9D6C4] shadow-xs dark:bg-[#181A20] dark:border-[#333742] dark:shadow-md'
                  }`}
                >
                  <div className="flex items-start justify-between gap-2 mb-1.5">
                    <span className="text-xs font-bold leading-tight text-[#2E0A12] dark:text-white">
                      {item.title}
                    </span>
                    {!item.read && (
                      <span className="w-2 h-2 rounded-full shrink-0 bg-[#800020] dark:bg-[#B6FF2E] shadow-[0_0_6px_#B6FF2E]" />
                    )}
                  </div>
                  <p className="text-[11px] leading-relaxed mb-2 text-[#6C3B45] dark:text-slate-300">
                    {item.description}
                  </p>
                  <div className="flex items-center justify-between text-[10px] text-[#8A6A72] dark:text-slate-400">
                    <span>{item.timestamp}</span>
                    {item.link && (
                      <span className="font-semibold flex items-center gap-0.5 text-[#800020] dark:text-[#B6FF2E]">
                        <span>View</span>
                        <ExternalLink size={10} />
                      </span>
                    )}
                  </div>
                </motion.div>
              ))}
            </div>

          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};
export default NotificationDrawer;

