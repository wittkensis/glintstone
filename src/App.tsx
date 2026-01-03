import { useState } from 'react'

function App() {
  const [count, setCount] = useState(0)

  return (
    <div className="bg-gradient-to-b from-slate-900 to-slate-800 min-h-screen flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-white mb-4">Glintstone</h1>
        <p className="text-xl text-slate-300 mb-8">Unlock Ancient Mesopotamia</p>
        <button
          onClick={() => setCount((count) => count + 1)}
          className="bg-amber-500 hover:bg-amber-600 text-white font-bold py-3 px-8 rounded-lg transition-colors"
        >
          count is {count}
        </button>
        <p className="text-slate-400 mt-4 text-sm">Project initialization in progress...</p>
      </div>
    </div>
  )
}

export default App
