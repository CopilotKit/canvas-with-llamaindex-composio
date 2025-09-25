"use client";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Sheet, Plus, RefreshCw, Link2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface GoogleSheetsMenuProps {
  className?: string;
  variant?: "default" | "outline";
  align?: "start" | "center" | "end";
  onAction?: (action: string) => void;
}

export default function GoogleSheetsMenu({ 
  className, 
  variant = "outline", 
  align = "center",
  onAction 
}: GoogleSheetsMenuProps) {
  const handleAction = (action: string) => {
    if (onAction) {
      onAction(action);
    } else {
      // Default behavior: fill chat input with the action
      const chatInput = document.querySelector('textarea[placeholder*="Type a message"]') as HTMLTextAreaElement;
      if (chatInput) {
        chatInput.value = action;
        chatInput.focus();
        // Trigger input event to update React state
        const event = new Event('input', { bubbles: true });
        chatInput.dispatchEvent(event);
      }
    }
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant={variant}
          className={cn("gap-2", className)}
          title="Google Sheets actions"
        >
          <Sheet className="h-4 w-4" />
          Google Sheets
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align={align} className="w-48">
        <DropdownMenuItem onClick={() => handleAction("Create a new Google Sheet")}>
          <Plus className="mr-2 h-4 w-4" />
          Create Sheet
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => handleAction("Sync all items to Google Sheets")}>
          <RefreshCw className="mr-2 h-4 w-4" />
          Sync to Sheets
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => handleAction("Get the Google Sheet URL")}>
          <Link2 className="mr-2 h-4 w-4" />
          Get Sheet URL
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
