type InputFieldProps = {
  label: string
  type: string
  value: string
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void
  required?: boolean
  minLength?: number
  autoFocus?: boolean
}

export default function InputField({
  label,
  type,
  value,
  onChange,
  required = false,
  minLength,
  autoFocus = false
}: InputFieldProps) {
  return (
    <div>
      <label htmlFor={label.toLowerCase()} className="block text-sm font-medium text-gray-700 dark:text-gray-300">
        {label}
      </label>
      <input
        id={label.toLowerCase()}
        name={label.toLowerCase()}
        type={type}
        value={value}
        onChange={onChange}
        required={required}
        minLength={minLength}
        autoFocus={autoFocus}
        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
      />
    </div>
  )
}