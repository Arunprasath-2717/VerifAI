import * as React from "react";
import { Check } from "lucide-react";
import { cn } from "../../lib/utils";

export interface CheckboxProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, "type" | "onChange"> {
  checked?: boolean;
  onCheckedChange?: (checked: boolean) => void;
}

const Checkbox = React.forwardRef<HTMLInputElement, CheckboxProps>(
  ({ className, checked = false, onCheckedChange, id, ...props }, ref) => {
    return (
      <div className="relative inline-flex items-center">
        <input
          type="checkbox"
          id={id}
          ref={ref}
          checked={checked}
          onChange={(e) => onCheckedChange?.(e.target.checked)}
          className="sr-only peer"
          {...props}
        />
        <label
          htmlFor={id}
          className={cn(
            "peer h-4 w-4 shrink-0 rounded border border-slate-300 dark:border-[#3E4555] bg-white dark:bg-[#1E2129] flex items-center justify-center cursor-pointer transition-all peer-focus-visible:outline-none peer-focus-visible:ring-2 peer-focus-visible:ring-[#B6FF2E]/40 peer-disabled:cursor-not-allowed peer-disabled:opacity-50",
            checked && "bg-[#181A20] dark:bg-[#B6FF2E] border-[#181A20] dark:border-[#B6FF2E] text-white dark:text-[#12141A]",
            className
          )}
        >
          {checked && (
            <Check className="h-3 w-3 stroke-[3]" />
          )}
        </label>
      </div>
    );
  }
);
Checkbox.displayName = "Checkbox";

export { Checkbox };
