import { forwardRef, useState, type ButtonHTMLAttributes } from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/shared/lib/utils';

const buttonVariants = cva(
  'inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-lg text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      variant: {
        default: 'bg-brand-600 text-white hover:bg-brand-700',
        destructive: 'bg-error text-white hover:bg-error/90',
        outline: 'border text-white',
        secondary: 'text-white',
        ghost: 'hover:text-white',
        link: 'text-brand-500 underline-offset-4 hover:underline',
      },
      size: {
        default: 'h-9 px-4 py-2',
        sm: 'h-8 rounded-md px-3 text-xs',
        lg: 'h-10 rounded-md px-8',
        icon: 'h-9 w-9',
      },
    },
    defaultVariants: { variant: 'default', size: 'default' },
  }
);

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement>, VariantProps<typeof buttonVariants> {}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, style, ...props }, ref) => {
    const [isHovered, setIsHovered] = useState(false);

    const baseStyle: React.CSSProperties = {};
    if (variant === 'outline') {
      baseStyle.borderColor = 'var(--border)';
      baseStyle.backgroundColor = isHovered ? 'var(--bg-card-hover)' : 'var(--bg-card)';
    } else if (variant === 'secondary') {
      baseStyle.backgroundColor = isHovered ? 'var(--bg-card-hover)' : 'var(--border)';
    } else if (variant === 'ghost') {
      baseStyle.color = isHovered ? undefined : 'var(--text-secondary)';
      baseStyle.backgroundColor = isHovered ? 'var(--bg-card-hover)' : undefined;
    }

    return (
      <button
        className={cn(buttonVariants({ variant, size }), className)}
        style={{ ...baseStyle, ...style } as React.CSSProperties}
        onMouseEnter={(e) => { setIsHovered(true); props.onMouseEnter?.(e); }}
        onMouseLeave={(e) => { setIsHovered(false); props.onMouseLeave?.(e); }}
        ref={ref}
        {...props}
      />
    );
  }
);
Button.displayName = 'Button';
