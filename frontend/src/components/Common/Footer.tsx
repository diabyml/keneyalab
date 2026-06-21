export function Footer() {
  const currentYear = new Date().getFullYear()

  return (
    <footer className="shrink-0 border-t border-border/65 bg-background/70 px-4 py-2">
      <div className="flex items-center justify-center">
        <p className="text-xs text-muted-foreground">
          KeneyaLab &middot; Système d'information de laboratoire &middot;{" "}
          {currentYear}
        </p>
      </div>
    </footer>
  )
}
