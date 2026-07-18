import { forwardRef, type HTMLAttributes } from 'react';
import { cn } from '@/shared/lib/utils';

export const Card = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, style, ...props }, ref) => (
    <div ref={ref}
      className={cn('rounded-lg border p-4', className)}
      style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border)', ...style }}
      {...props} />
  )
);
Card.displayName = 'Card';

export const CardHeader = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn('flex flex-col space-y-1.5 pb-3', className)} {...props} />
  )
);
CardHeader.displayName = 'CardHeader';

export const CardTitle = forwardRef<HTMLParagraphElement, HTMLAttributes<HTMLHeadingElement>>(
  ({ className, style, ...props }, ref) => (
    <h3 ref={ref}
      className={cn('font-semibold leading-none tracking-tight', className)}
      style={{ color: 'var(--text-primary)', ...style }}
      {...props} />
  )
);
CardTitle.displayName = 'CardTitle';

export const CardContent = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn('pt-0', className)} {...props} />
  )
);
CardContent.displayName = 'CardContent';
