export function Footer() {
  const currentYear = new Date().getFullYear()

  return (
    <footer className="shrink-0 border-t px-4 py-2">
      <div className="flex items-center justify-center">
        <p className="text-xs text-muted-foreground">
          KeneyaLab &mdash; {currentYear}
        </p>
      </div>
    </footer>
  )
}
