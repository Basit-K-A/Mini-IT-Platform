interface ErrorMessageProps {
  message: string
}

export function ErrorMessage({ message }: ErrorMessageProps) {
  if (!message) return null
  return (
    <div className="error-banner" role="alert">
      {message}
    </div>
  )
}
