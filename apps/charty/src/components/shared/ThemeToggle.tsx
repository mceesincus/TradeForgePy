// src/components/shared/ThemeToggle.tsx
import * as React from "react"
import { Moon, Sun } from "lucide-react" // Using lucide-react icons
import { useTheme } from "next-themes"

import { Button } from "@/components/ui/button"

export function ThemeToggle() {
  // We will use a cycle: light -> dark -> very-dark -> light
  const { theme, setTheme } = useTheme()

  const toggleTheme = () => {
    if (theme === "light") {
      setTheme("dark")
    } else if (theme === "dark") {
      setTheme("very-dark")
    } else {
      setTheme("light")
    }
  }

  return (
    <Button variant="ghost" size="icon" onClick={toggleTheme}>
      <Sun className="h-[1.2rem] w-[1.2rem] rotate-0 scale-100 transition-all dark:hidden very-dark:hidden" />
      <Moon className="h-[1.2rem] w-[1.2rem] rotate-0 scale-100 transition-all hidden dark:inline-block very-dark:hidden" />
      <Moon className="h-[1.2rem] w-[1.2rem] rotate-90 scale-100 transition-all hidden very-dark:inline-block" />
      <span className="sr-only">Toggle theme</span>
    </Button>
  )
}