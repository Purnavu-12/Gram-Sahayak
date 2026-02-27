import { useTranslation } from 'react-i18next'
import { useSpeech } from '../hooks/useSpeech'

interface SpeakButtonProps {
  /** The text to read aloud */
  text: string
  /** Optional: smaller inline variant */
  inline?: boolean
}

export default function SpeakButton({ text, inline }: SpeakButtonProps) {
  const { t } = useTranslation()
  const { speak, stop, speaking, supported } = useSpeech()

  if (!supported) return null

  const handleClick = () => {
    if (speaking) {
      stop()
    } else {
      speak(text)
    }
  }

  return (
    <button
      className={`speak-btn ${inline ? 'speak-btn-inline' : ''} ${speaking ? 'speaking' : ''}`}
      onClick={handleClick}
      aria-label={speaking ? t('common.stop_speaking') : t('common.speak')}
      title={speaking ? t('common.stop_speaking') : t('common.speak')}
      type="button"
    >
      {speaking ? '⏹️' : '🔊'}
      {!inline && (
        <span className="speak-label">
          {speaking ? t('common.stop_speaking') : t('common.speak')}
        </span>
      )}
    </button>
  )
}
