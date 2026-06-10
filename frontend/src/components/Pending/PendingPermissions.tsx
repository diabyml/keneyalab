function PendingPermissions() {
  return (
    <div className="flex flex-col gap-3">
      {Array.from({ length: 8 }).map((_, i) => (
        <div
          key={i}
          className="h-10 w-full animate-pulse rounded-md bg-muted"
        />
      ))}
    </div>
  )
}

export default PendingPermissions
