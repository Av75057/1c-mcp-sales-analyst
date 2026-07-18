import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/shared/lib/utils';

const badgeVariants = cva(
  'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium transition-colors',
  {
    variants: {
      variant: {
        default: 'bg-brand-500/20 text-brand-500',
        secondary: '',
        success: 'bg-success/20 text-success',
        warning: 'bg-warning/20 text-warning',
        error: 'bg-error/20 text-error',
      },
    },
    defaultVariants: { variant: 'default' },
  }
);

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement>, VariantProps<typeof badgeVariants> {}

const variantStyles: Record<string, React.CSSProperties> = {
  secondary: { backgroundColor: 'var(--border)', color: 'var(--text-secondary)' },
};

export function Badge({ className, variant, style, ...props }: BadgeProps) {
  return (
    <span
      className={cn(badgeVariants({ variant }), className)}
      style={{ ...(variant && variantStyles[variant]), ...style } as React.CSSProperties}
      {...props}
    />
  );
}
