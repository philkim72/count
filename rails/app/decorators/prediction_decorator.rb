class PredictionDecorator < ApplicationDecorator
  delegate_all

  def density_map_tag
    if object.density_map
      h.link_to(object.density_map.url) do
        h.ix_image_tag(object.density_map.url, { sizes: "180px", class: "densitymaphook" })
      end
    end
  end

  def created_at
    l object.created_at, format: :calendar_timezone
  end

  def crowd_count
    h.number_with_precision object.crowd_count, precision: 2
  end

  def line_count
    h.number_with_precision object.line_count, precision: 2
  end

  def admin_cell
    return unless density_map_tag.present?
    density_map_tag&.html_safe +
      h.content_tag(:span) do
        h.content_tag(:h6, "Crowd") + crowd_count
      end + h.content_tag(:span) do
        h.content_tag(:h6, "Line") + (line_count.presence || "NA")
      end + h.content_tag(:span) do
        h.content_tag(:h6, "Ver") + version
      end
  end
end
