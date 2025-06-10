// tailwind.config.js
module.exports = {
	theme: {
		extend: {
			colors: {
				bg: '#0A0A0B',
				surface: { 
					DEFAULT: '#1A1B1D', 
					2: '#222327',
					3: '#2A2B2F'
				},
				border: '#32343A',
				text: { 
					primary: '#F5F5F5', 
					secondary: '#A6A6AD',
					muted: '#8A8A90'
				},
				accent: { 
					DEFAULT: '#9EA6FF', 
					hover: '#636BFF',
					muted: '#6B6F8F'
				},
				success: '#4DD88B',
				error: '#FF5F6C'
			},
			boxShadow: {
				'retro': '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
				'retro-lg': '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
			},
			borderRadius: {
				'retro': '0.5rem',
				'retro-lg': '0.75rem',
			}
		}
	}
};
