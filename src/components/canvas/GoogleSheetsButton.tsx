"use client";

import { Button } from "@/components/ui/button";
import { Sheet } from "lucide-react";
import { cn } from "@/lib/utils";
import { useCopilotChat } from "@copilotkit/react-core";

interface GoogleSheetsButtonProps {
  className?: string;
  variant?: "default" | "outline";
}

export default function GoogleSheetsButton({ className, variant = "outline" }: GoogleSheetsButtonProps) {
  const { appendMessage } = useCopilotChat();

  const handleClick = () => {
    // Send message to agent to sync with Google Sheets
    appendMessage({
      role: "user",
      content: "Sync all items to Google Sheets"
    });
  };

  return (
    <Button
      variant={variant}
      className={cn("gap-2", className)}
      onClick={handleClick}
    >
      <Sheet className="h-4 w-4" />
      Google Sheets
    </Button>
  );
}
