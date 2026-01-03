import type { Tablet } from '../../types'

type TabletSurface = 'obverse' | 'reverse'

interface TabletViewerProps {
  tablet: Tablet
  surface?: TabletSurface
  onSurfaceChange?: (surface: TabletSurface) => void
  className?: string
}

/**
 * TabletViewer - Displays a tablet image (basic, no zoom/pan for MVP).
 * The visual centerpiece of the Glintstone platform.
 */
export function TabletViewer({
  tablet,
  surface = 'obverse',
  onSurfaceChange,
  className = ''
}: TabletViewerProps) {
  const imageUrl = surface === 'obverse'
    ? tablet.images.obverse
    : tablet.images.reverse

  return (
    <figure
      className={`
        relative bg-[#1a1a1a] rounded-lg overflow-hidden
        ${className}
      `.trim()}
      aria-label={`Tablet viewer: ${tablet.cdli_id}`}
    >
      {/* Viewport */}
      <div
        className="relative min-h-[300px] flex items-center justify-center overflow-hidden"
        role="img"
        aria-label={`${tablet.museum_number}, ${tablet.period} ${tablet.genre}`}
      >
        {imageUrl ? (
          <img
            src={imageUrl}
            alt={`${surface} of tablet ${tablet.cdli_id}`}
            className="max-w-[80%] max-h-[280px] object-contain select-none pointer-events-none"
          />
        ) : (
          // Placeholder when no image available
          <div
            className="w-[200px] h-[250px] rounded bg-gradient-to-br from-[#d4a574] via-[#c4956a] to-[#b38560] flex flex-col items-center justify-center shadow-[inset_0_0_30px_rgba(0,0,0,0.2)]"
          >
            <span className="text-[#5c4a3a] text-sm mt-20">
              {tablet.cdli_id}
            </span>
          </div>
        )}
      </div>

      {/* Surface tabs */}
      {onSurfaceChange && (
        <div
          className="flex gap-1 p-3 bg-black/50"
          role="tablist"
          aria-label="Tablet surfaces"
        >
          <button
            role="tab"
            aria-selected={surface === 'obverse'}
            onClick={() => onSurfaceChange('obverse')}
            className={`
              px-3 py-2 border-none rounded text-sm cursor-pointer transition-all
              ${surface === 'obverse'
                ? 'bg-[rgb(var(--accent))] text-black'
                : 'bg-white/10 text-white hover:bg-white/20'}
            `}
          >
            Obverse
          </button>
          <button
            role="tab"
            aria-selected={surface === 'reverse'}
            onClick={() => onSurfaceChange('reverse')}
            className={`
              px-3 py-2 border-none rounded text-sm cursor-pointer transition-all
              ${surface === 'reverse'
                ? 'bg-[rgb(var(--accent))] text-black'
                : 'bg-white/10 text-white hover:bg-white/20'}
            `}
          >
            Reverse
          </button>
        </div>
      )}

      {/* Caption */}
      <figcaption className="p-2 px-4 bg-black/70 text-white text-sm text-center">
        {tablet.museum_number} - {tablet.period} {tablet.genre}
      </figcaption>
    </figure>
  )
}
