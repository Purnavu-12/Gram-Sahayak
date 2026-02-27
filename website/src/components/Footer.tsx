import { useTranslation } from 'react-i18next'

export default function Footer() {
  const { t } = useTranslation()

  return (
    <footer className="footer">
      <div>{t('footer.text')}</div>
      <div className="footer-links">
        <a href="#">{t('footer.privacy')}</a>
        <a href="#">{t('footer.terms')}</a>
        <span>{t('footer.govt')}</span>
      </div>
    </footer>
  )
}
