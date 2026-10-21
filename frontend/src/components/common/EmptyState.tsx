import React, { ReactNode } from 'react';
import { Database, AlertCircle } from 'lucide-react';

interface EmptyStateProps {
  title: string;
  description: string;
  icon?: ReactNode;
  actionText?: string;
  onAction?: () => void;
  statusBadge?: string;
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title,
  description,
  icon,
  actionText,
  onAction,
  statusBadge,
  className = '',
}) => {
  return (
    <div
      className={`flex flex-col items-center justify-center p-8 text-center rounded-xl border border-slate-200 bg-white shadow-sm ${className}`}
    >
      <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center text-slate-500 mb-3">
        {icon || <Database className="w-6 h-6 text-slate-400" />}
      </div>
      {statusBadge && (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-50 text-amber-800 border border-amber-200 mb-2">
          <AlertCircle className="w-3 h-3 text-amber-600" />
          {statusBadge}
        </span>
      )}
      <h4 className="text-base font-semibold text-slate-800 mb-1">{title}</h4>
      <p className="text-sm text-slate-500 max-w-md mb-4">{description}</p>
      {actionText && onAction && (
        <button
          onClick={onAction}
          className="px-4 py-2 text-xs font-medium text-teal-700 bg-teal-50 hover:bg-teal-100 rounded-lg transition-colors border border-teal-200"
        >
          {actionText}
        </button>
      )}
    </div>
  );
};
