import * as React from "react";
import { cn } from "../../lib/utils";

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "destructive" | "outline" | "secondary" | "ghost" | "link" | "lime" | "liquid" | "liquidSecondary";
  size?: "default" | "sm" | "lg" | "icon";
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "default", size = "default", ...props }, ref) => {
    const variantStyles = {
      default:
        "bg-primary text-primary-foreground shadow hover:bg-primary/90 dark:bg-[#B6FF2E] dark:text-[#12141A] dark:hover:bg-[#A3E823] dark:shadow-[0_0_20px_rgba(182,255,46,0.35)]",
      lime:
        "bg-[#B6FF2E] text-[#12141A] font-bold hover:bg-[#A3E823] shadow-[0_0_20px_rgba(182,255,46,0.35)] active:scale-[0.99]",
      destructive:
        "bg-destructive text-destructive-foreground shadow-sm hover:bg-destructive/90",
      outline:
        "border border-input bg-background shadow-sm hover:bg-accent hover:text-accent-foreground dark:border-[#2E3340] dark:bg-[#1E2129] dark:hover:bg-[#252934] dark:text-white",
      secondary:
        "bg-secondary text-secondary-foreground shadow-sm hover:bg-secondary/80",
      ghost: "hover:bg-accent hover:text-accent-foreground dark:hover:bg-[#1E2129]",
      link: "text-primary underline-offset-4 hover:underline dark:text-[#B6FF2E]",
      liquid: "verifai-auth-btn-primary",
      liquidSecondary: "verifai-auth-btn-secondary",
    };

    const sizeStyles = {
      default: "h-11 px-4 py-2",
      sm: "h-9 rounded-lg px-3 text-xs",
      lg: "h-12 rounded-xl px-8 text-base",
      icon: "h-10 w-10",
    };

    return (
      <button
        className={cn(
          "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-xl text-sm font-semibold transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 cursor-pointer active:scale-[0.99]",
          variantStyles[variant],
          sizeStyles[size],
          className
        )}
        ref={ref}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";

export { Button };
