interface UserStatusToggleProps {
  value: boolean;
  onChange: (value: boolean) => void;
}

export const UserStatusToggle: React.FC<UserStatusToggleProps> = ({ value, onChange }) => {
  return (
    <div className="flex items-center gap-3">
      <label className="relative inline-flex items-center cursor-pointer">
        <input
          type="checkbox"
          checked={value}
          onChange={(e) => onChange(e.target.checked)}
          className="sr-only peer"
        />
        <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-[#4ade80]/30 rounded-full peer peer-checked:bg-[#4ade80]"></div>
        <div className="absolute left-1 top-1 bg-white w-4 h-4 rounded-full transition peer-checked:translate-x-5"></div>
      </label>
      <span className="text-sm font-medium">{value ? 'Active' : 'Disabled'}</span>
    </div>
  );
};