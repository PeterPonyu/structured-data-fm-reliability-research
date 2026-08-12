# Reusable professional ggplot2 theme + helpers for the reliability-portfolio manuscripts.
# Usage in a figure script:
#   source("${ORCHESTRATION_FILES}/manuscript-template/ggtheme.R")
#   d <- read_result("/path/to/result.json")          # jsonlite
#   p <- ggplot(...) + theme_paper()
#   save_fig(p, "figures/F1_name", w = 6.5, h = 4)     # writes 300-dpi PNG + PDF
suppressMessages({
  library(ggplot2)
  library(jsonlite)
  library(scales)
})

# Serif family for all figure text so the PDFs match the LaTeX body font.
# "Nimbus Roman" (URW Times clone) is present system-wide; cairo_pdf embeds it
# as a proper serif subset (no Type 3, no sans fallback). Overridable via env.
PAPER_FONT <- Sys.getenv("PAPER_FONT", "Nimbus Roman")
# Route the serif family onto every text-bearing geom (text/label used by
# annotate()) so no default sans slips into a panel.
update_geom_defaults("text",  list(family = PAPER_FONT))
update_geom_defaults("label", list(family = PAPER_FONT))

# Okabe-Ito colorblind-safe palette
okabe_ito <- c("#0072B2", "#E69F00", "#009E73", "#D55E00",
               "#CC79A7", "#56B4E9", "#F0E442", "#000000")

## Uniform typographic hierarchy (standing figure-typography rule): every
## title/axis/tick/annotation size sits within 1pt of base_size -- ticks and
## legend text are the deliberate 1pt-smaller step, nothing else. All text is
## black; the ONLY bold element permitted anywhere in a figure is the panel
## tag (A/B/C...), which is also nudged left via plot.tag.position so it
## clears a rotated y-axis title instead of crowding it.
theme_paper <- function(base_size = 11) {
  theme_bw(base_size = base_size, base_family = PAPER_FONT) +
    theme(
      panel.grid.minor  = element_blank(),
      panel.grid.major  = element_line(linewidth = 0.25, colour = "grey88"),
      panel.border      = element_rect(linewidth = 0.4, colour = "grey40"),
      strip.background  = element_rect(fill = "grey92", colour = NA),
      strip.text        = element_text(size = base_size, colour = "black"),
      axis.title        = element_text(size = base_size, colour = "black"),
      axis.text         = element_text(size = base_size - 1, colour = "black"),
      legend.position   = "bottom",
      legend.key        = element_blank(),
      legend.title      = element_text(size = base_size, colour = "black"),
      legend.text       = element_text(size = base_size - 1, colour = "black"),
      plot.title        = element_text(size = base_size, colour = "black"),
      plot.tag          = element_text(size = base_size, face = "bold", colour = "black"),
      plot.tag.position = c(-0.045, 1.03),
      plot.caption      = element_text(size = base_size - 1, colour = "grey40"),
      plot.margin       = margin(t = 5.5, r = 5.5, b = 5.5, l = 14)
    )
}

# Shared multi-panel tag theme: every patchwork composition (F3, F4, F5) adds
# this after `+ plot_annotation(tag_levels = "A")` so the bold/position rule
# is centralised instead of re-typed per figure. Tags sit in the margin,
# outside the panel spine; left/top plot.margin must be large enough that
# the tag is not clipped by the device.
paper_tag_theme <- theme(
  plot.tag          = element_text(family = PAPER_FONT, face = "bold",
                                    size = 11, colour = "black"),
  plot.tag.position = c(-0.02, 1.04),
  plot.margin       = margin(t = 12, r = 8, b = 6, l = 16)
)

# Human-readable dataset / model / ACS / RAC1P labels (never plot OpenML ids).
PRETTY_DATASET <- c(
  electricity              = "Electricity",
  eucalyptus               = "Eucalyptus",
  adult                    = "Adult",
  "cylinder-bands"         = "Cylinder bands",
  churn                    = "Churn",
  Moneyball                = "Moneyball",
  kick                     = "Kick",
  black_friday             = "Black Friday",
  house_prices_nominal     = "House prices",
  colleges                 = "Colleges",
  Airlines_DepDelay_10M    = "Airline delays",
  "nyc-taxi-green-dec-2016"= "NYC taxi",
  house_sales              = "House sales",
  "sf-police-incidents"    = "SF police"
)
PRETTY_MODEL <- c(
  lightgbm = "LightGBM",
  xgboost  = "XGBoost",
  LightGBM = "LightGBM",
  XGBoost  = "XGBoost",
  TabICLv2 = "TabICLv2",
  TabDPT   = "TabDPT"
)
PRETTY_ACS <- c(
  ACSEmployment      = "Employment",
  ACSIncome          = "Income",
  ACSPublicCoverage  = "Pub. cov.",
  ACSMobility        = "Mobility"
)
# Folktables RAC1P codes present in the frozen ACS arm (1, 2, 6, 8, 9).
PRETTY_RAC1P <- c(
  "1" = "White",
  "2" = "Black",
  "6" = "Asian",
  "8" = "Other",
  "9" = "Two or more"
)
pretty_map <- function(x, table) {
  x <- as.character(x)
  y <- unname(table[x])
  ifelse(is.na(y), x, y)
}
pretty_dataset <- function(x) pretty_map(x, PRETTY_DATASET)
pretty_model   <- function(x) pretty_map(x, PRETTY_MODEL)
pretty_acs     <- function(x) pretty_map(x, PRETTY_ACS)
pretty_rac1p   <- function(x) pretty_map(x, PRETTY_RAC1P)

scale_color_paper <- function(...) scale_colour_manual(values = okabe_ito, ...)
scale_fill_paper  <- function(...) scale_fill_manual(values = okabe_ito, ...)

# Read a result JSON; returns a nested list.
read_result <- function(path) jsonlite::fromJSON(path, simplifyVector = FALSE)

# Save a figure at publication size as BOTH 300-dpi PNG and vector PDF.
save_fig <- function(plot, stem, w = 6.5, h = 4) {
  dir.create(dirname(stem), showWarnings = FALSE, recursive = TRUE)
  ggsave(paste0(stem, ".png"), plot, width = w, height = h, dpi = 300, bg = "white")
  ggsave(paste0(stem, ".pdf"), plot, width = w, height = h, device = cairo_pdf, bg = "white")
  invisible(stem)
}
