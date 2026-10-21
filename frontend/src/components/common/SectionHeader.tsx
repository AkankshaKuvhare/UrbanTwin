import React, { ReactNode } from 'react';

interface SectionHeaderProps {
  title: string;
  subtitle?: string;
  tag?: string;
  actions?: ReactNode;
  className?: string;
}

export const SectionHeader: React.FC<SectionHeaderProps> = ({
  title,
  subtitle,
  tag,
  actions,
  className = '',
}) => {
  return (
    <div className={`flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-6 ${className}`}>
      <div>
        <div className="flex items-center gap-2">
          <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900">
            {title}
          </h2>
          {tag && (
            <span className="px-2 py-0.5 text-xs font-semibold rounded-md bg-teal-50 text-teal-700 border border-teal-200">
              {tag}
            </span>
          )}
        </div>
        {subtitle && (
          <p className="text-xs sm:text-sm text-slate-500 mt-1 max-w-2xl leading-relaxed">
            {subtitle}
          </p>
        )}
      </div>
      {actions && <div className="flex items-center gap-2 flex-wrap">{actions}</div>}
    </div>
  );
};
