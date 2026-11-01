import * as React from "react";
import { cn } from "../../lib/utils";

export interface LabelProps
  extends React.LabelHTMLAttributes<HTMLLabelElement> {}

const Label = React.forwardRef<HTMLLabelElement, LabelProps>(
  ({ className, ...props }, ref) => (
    <label
      ref={ref}
      className={cn(
        "text-sm sm:text-[15px] font-semibold leading-none text-slate-800 dark:text-slate-200 peer-disabled:cursor-not-allowed peer-disabled:opacity-70 select-none",
        className
      )}
      {...props}
    />
  )
);
Label.displayName = "Label";

export { Label };
