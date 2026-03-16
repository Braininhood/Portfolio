import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { TIMEZONE_OPTIONS } from "@/utils/timezone";

interface TimezoneSelectProps {
  value: string;
  onValueChange: (value: string) => void;
  label?: string;
  placeholder?: string;
  id?: string;
  className?: string;
  disabled?: boolean;
}

export function TimezoneSelect({
  value,
  onValueChange,
  label = "Time zone",
  placeholder = "Select your time zone",
  id = "timezone",
  className,
  disabled,
}: TimezoneSelectProps) {
  return (
    <div className={className}>
      {label && <Label htmlFor={id} className="text-xs sm:text-sm">{label}</Label>}
      <Select value={value ?? ""} onValueChange={onValueChange} disabled={disabled}>
        <SelectTrigger id={id} className="h-9 sm:h-10 text-sm mt-1">
          <SelectValue placeholder={placeholder} />
        </SelectTrigger>
        <SelectContent>
          {TIMEZONE_OPTIONS.map((opt) => (
            <SelectItem key={opt.value} value={opt.value}>
              {opt.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
