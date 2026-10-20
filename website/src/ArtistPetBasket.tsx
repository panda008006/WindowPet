import type { CSSProperties, MouseEvent } from 'react'
import { Download, Eye, Sparkles, Heart, Info, ArrowUpRight } from 'lucide-react'
import type { GalleryPet, PetAuthor } from './galleryData'

export interface ArtistPetBasketProps {
  author: PetAuthor
  pets: GalleryPet[]
  onSelectPet: (pet: GalleryPet) => void
  onImportPet: (pet: GalleryPet) => void
  onCommissionClick?: () => void
  isFavorite?: (petId: string) => boolean
  onToggleFavorite?: (e: MouseEvent, petId: string) => void
}

export function ArtistPetBasket({
  author,
  pets,
  onSelectPet,
  onImportPet,
  onCommissionClick,
  isFavorite,
  onToggleFavorite,
}: ArtistPetBasketProps) {
  return (
    <section className="artist-pet-basket-section" aria-label={`${author.name}的作品筐`}>
      {/* 实体收纳筐大容器 */}
      <div className="artist-basket-container" style={{ '--author-theme-color': author.badgeColor } as CSSProperties}>
        {/* 1. 筐体顶部加固木沿与双侧藤编耳提手 */}
        <div className="basket-top-structure">
          <div className="basket-ear-handle basket-ear-left" title="藤编手提耳" />
          <div className="basket-rim-beam">
            <div className="basket-rim-texture" />
            <div className="basket-rim-brass-nail nail-left" />
            <div className="basket-rim-brass-nail nail-right" />
          </div>
          <div className="basket-ear-handle basket-ear-right" title="藤编手提耳" />
        </div>

        {/* 2. 筐口自然外翻的棉麻衬布 (Linen Fabric Drape) */}
        <div className="basket-linen-drape">
          <div className="linen-fold-pattern" />
          <div className="linen-scallop-hem" />

          {/* 挂绳皮质/木质专属工坊名牌 (Hanging Tag) */}
          <div className="basket-wooden-tag">
            <div className="tag-string" />
            <div className="tag-card">
              <span className="tag-icon">🧺</span>
              <div className="tag-texts">
                <div className="tag-main-row">
                  <strong>【{author.name}】的萌宠手作筐</strong>
                  <span className="tag-count-pill">盛装 {pets.length} 款伙伴</span>
                </div>
                <div className="tag-sub-row">
                  <span className="tag-highlight">100% 永久免费 · 免登录即取即用</span>
                  <span className="tag-hint">💡 点击任意角色即可开箱把玩全套动作</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 3. 筐内温润软垫展床 (Basket Interior Bed) */}
        <div className="basket-interior-bed">
          {pets.length === 0 ? (
            <div className="basket-empty-state">
              <Info size={36} color="#94a3b8" />
              <h4>作品筐暂时空空如也</h4>
              <p>画师正在手绘赶稿打磨中，敬请期待！</p>
            </div>
          ) : (
            <div className="basket-pets-grid">
              {pets.map((pet) => {
                const fav = isFavorite ? isFavorite(pet.id) : false
                const previewImg = `${import.meta.env.BASE_URL}${pet.animatedWebp || pet.image}`

                return (
                  <article
                    key={pet.id}
                    className="basket-pet-card"
                    onClick={() => onSelectPet(pet)}
                    role="button"
                    tabIndex={0}
                    onKeyDown={(e) => e.key === 'Enter' && onSelectPet(pet)}
                    title={`点击开箱查看【${pet.name}】动作详情`}
                  >
                    {/* 收藏按钮 */}
                    {onToggleFavorite && (
                      <button
                        type="button"
                        className={`basket-fav-btn ${fav ? 'is-fav' : ''}`}
                        onClick={(e) => onToggleFavorite(e, pet.id)}
                        title={fav ? '取消收藏' : '加入收藏'}
                      >
                        <Heart size={14} fill={fav ? '#e11d48' : 'none'} color={fav ? '#e11d48' : '#64748b'} />
                      </button>
                    )}

                    {/* 软窝展台与微浮动效角色 */}
                    <div className="basket-pet-cushion">
                      <div className="cushion-halo" />
                      <img
                        src={previewImg}
                        alt={pet.name}
                        className="basket-pet-sprite"
                        loading="lazy"
                      />
                      <span className="basket-pet-action-count">
                        <Sparkles size={11} />
                        <span>{pet.actionCount || pet.actions?.length || 3} 动作</span>
                      </span>
                    </div>

                    {/* 角色信息与标签 */}
                    <div className="basket-pet-meta">
                      <h4 className="basket-pet-name">{pet.name}</h4>
                      <p className="basket-pet-tagline">{pet.tagline || '轻快活泼的桌面伙伴'}</p>

                      <div className="basket-pet-tags">
                        <span className="basket-tag-pill">单击互动</span>
                        <span className="basket-tag-pill">悬空拖拽</span>
                        <span className="basket-tag-pill">伴读待机</span>
                      </div>
                    </div>

                    {/* 卡片底部操作栏 */}
                    <div className="basket-card-bottom-bar">
                      <button
                        type="button"
                        className="basket-inspect-btn"
                        onClick={(e) => {
                          e.stopPropagation()
                          onSelectPet(pet)
                        }}
                        title="查看全部动作试玩"
                      >
                        <Eye size={13} />
                        <span>开箱试玩</span>
                      </button>

                      <button
                        type="button"
                        className="basket-direct-import-btn"
                        onClick={(e) => {
                          e.stopPropagation()
                          onImportPet(pet)
                        }}
                        title={`一键呼叫客户端导入【${pet.name}】`}
                      >
                        <Download size={13} />
                        <span>导入</span>
                      </button>
                    </div>
                  </article>
                )
              })}
            </div>
          )}

          {/* 筐底贴心结语与定制通道 */}
          <div className="basket-floor-bar">
            <div className="basket-floor-info">
              <span className="floor-badge">🧺 原创正版保障</span>
              <span className="floor-desc">
                以上 {pets.length} 款作品均为画师原画手工切帧制作，支持在 WindowPet 桌面端自由调整大小、拖拽与互动。
              </span>
            </div>
            {author.acceptCustom && onCommissionClick && (
              <button
                type="button"
                className="basket-commission-fast-btn"
                onClick={onCommissionClick}
                title="联系该画师定制专属爱宠"
              >
                <span>约该作者 1 对 1 手绘定制 (￥88)</span>
                <ArrowUpRight size={14} />
              </button>
            )}
          </div>
        </div>
      </div>
    </section>
  )
}
