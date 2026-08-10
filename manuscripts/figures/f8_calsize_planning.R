# F8: calibration-size PLANNING CURVE for the Mondrian remedy (4 panels).
#
# Reads ONLY experiments/calsize_planning_2026-08-01/results.json (frozen) plus
# the frozen reconciled diagnostic for panel D's cross-sectional reference.
#
# HONESTY NOTE -- this figure reports a NEGATIVE result and must not be drawn to
# imply otherwise. The designed within-dataset sweep does NOT reproduce the
# cross-sectional dose-response:
#   * helps side (panel A): median Spearman rho = 0.00, positive in 2/6 series,
#     and the two GBM arms disagree in SIGN on the same dataset (electricity
#     -0.90 vs +0.90). So panel A gets NO trend line -- a fitted slope through
#     sign-disagreeing series would manufacture a relationship that is not there.
#   * hurts side (panel B): median rho = -0.51, negative in 5/6 -- added
#     calibration mass makes Mondrian WORSE where it already hurts. This one is
#     directional and stable, so panel B does carry a per-series line.
# Panel D shows the frozen cross-sectional cut (rho=+0.497, threshold 352) that
# the within-dataset sweep fails to reproduce -- the Simpson-style reversal is
# the whole point of the figure, so D is drawn adjacent to A/B deliberately.
cargs <- commandArgs(trailingOnly = FALSE)
SDIR  <- dirname(normalizePath(sub("^--file=", "", cargs[grep("^--file=", cargs)][1])))
source(Sys.getenv("GGTHEME_R", file.path(SDIR, "ggtheme.R")))
library(patchwork)

REPO <- normalizePath(file.path(SDIR, "..", ".."))
PLAN <- read_result(file.path(REPO, "experiments", "calsize_planning_2026-08-01",
                              "results.json"))
DIA  <- read_result(file.path(REPO, "experiments", "results",
                              "nd1_s2_p4_calsize_diag_reconciled.json"))

num <- function(x) if (is.null(x)) NA_real_ else suppressWarnings(as.numeric(x))
g   <- function(r, k) if (!is.null(r[[k]])) r[[k]] else NA

PRIMARY <- "floor1"

# ---- per-cell rows (dataset x model x frac x seed x rule) -------------------
cells <- do.call(rbind, lapply(PLAN$rows, function(r) data.frame(
  name   = as.character(g(r, "name")),
  model  = as.character(g(r, "model")),
  rule   = as.character(g(r, "rule")),
  side   = as.character(g(r, "side")),
  frac   = num(g(r, "frac")),
  seed   = num(g(r, "seed")),
  mass   = num(g(r, "uncbin_cal_median")),
  mond   = num(g(r, "mondrian_improvement_med")),
  # "inert" is DERIVED, not a stored field: when every active uncertainty bin
  # falls back to the marginal quantile, Mondrian IS split conformal and the
  # improvement is identically 0 by construction (a floor artefact, not a
  # neutral measurement).
  nbin   = num(g(r, "n_uncbins_active")),
  nfall  = num(g(r, "n_uncbins_fallback_marginal")),
  stringsAsFactors = FALSE)))
cells <- cells[cells$rule == PRIMARY & is.finite(cells$mass) & is.finite(cells$mond), ]
cells$inert <- is.finite(cells$nbin) & is.finite(cells$nfall) & cells$nfall == cells$nbin

# ---- panels A/B: dose-response, LightGBM (the reproduction-anchored arm) ----
# LightGBM is the arm whose frac=1.0 seed-0 cells reproduce the frozen Stage-2
# record bit-exactly (6/6), so it is the arm the curve is quoted on.
lgb <- cells[cells$model == "lightgbm", ]
# across-seed median per (dataset, frac): the plotted point
agg_med <- aggregate(cbind(mass, mond) ~ name + side + frac, data = lgb, FUN = median)

# ONE dataset -> ONE colour, fixed across A/B/C. Each panel plots a different
# subset (A three datasets, B three, C all six), and a per-panel scale assigns
# the palette in order of whatever levels that subset happens to contain, so
# electricity came out green in A and orange in C. Keying the palette to the
# sorted union makes a dataset's hue mean the same thing in every panel.
DS_ALL <- sort(unique(lgb$name))
DS_COL <- setNames(okabe_ito[seq_along(DS_ALL)], DS_ALL)
scale_ds_colour <- function() scale_colour_manual(values = DS_COL, na.value = "grey60")
scale_ds_fill   <- function() scale_fill_manual(values = DS_COL, na.value = "grey60")

# A cell is inert when every active bin fell back to the marginal quantile, so
# Mondrian IS split conformal and the 0.0000 is true by construction. Plotted
# hollow: filled = measured, hollow = definitional zero. Without this the two
# inert cells sit on the zero line and read as "no effect was found".
agg_med <- merge(agg_med,
  aggregate(inert ~ name + frac, data = lgb, FUN = function(z) mean(z) == 1),
  by = c("name", "frac"))

# Per-bin mass is NOT proportional to the fraction retained: on the small
# datasets the binner spends extra calibration rows on MORE bins, so mass stays
# pinned (cylinder-bands 6->11, adult 6->11, Moneyball 11->17 across a 10x
# sweep). Joining those points would draw a trajectory along an axis that never
# moved. Lines are therefore restricted to series whose mass actually spans >=3x.
span <- tapply(agg_med$mass, agg_med$name, function(m) max(m) / min(m))
agg_med$responsive <- span[agg_med$name] >= 3

dose_panel <- function(d, ttl) {
  p <- ggplot(d, aes(mass, mond, colour = name, fill = name, group = name)) +
    geom_hline(yintercept = 0, linetype = 3, colour = "grey50")
  if (any(d$responsive))
    p <- p + geom_line(data = d[d$responsive, ], linewidth = 0.5)
  p + geom_point(aes(shape = inert), size = 2.2, stroke = 0.7) +
    scale_shape_manual(values = c(`FALSE` = 21, `TRUE` = 1), guide = "none") +
    scale_x_log10() + scale_ds_colour() + scale_ds_fill() +
    labs(title = ttl,
         x = "per-bin calibration mass reached (log)",
         y = "Mondrian coverage improvement", colour = NULL, fill = NULL) +
    guides(colour = guide_legend(nrow = 1), fill = guide_legend(nrow = 1)) +
    theme_paper() + theme(legend.position = "bottom")
}
# Per-series lines join ONE dataset's own five levels, so they display that
# dataset's trajectory rather than fitting anything. What is deliberately absent
# from A and B is a regression ACROSS series: with the two GBM arms disagreeing
# in sign on the same dataset, a pooled slope would manufacture a trend.
# Titles stay descriptive; the verdict and its numbers live in the caption.
f8a <- dose_panel(agg_med[agg_med$side == "helps", ],
                  "Datasets where Mondrian helps")
f8b <- dose_panel(agg_med[agg_med$side == "hurts", ],
                  "Datasets where Mondrian hurts")

# ---- panel C: across-seed envelope (min/max band per dataset x frac) -------
env <- do.call(rbind, lapply(split(lgb, list(lgb$name, lgb$frac), drop = TRUE),
  function(d) data.frame(
    name = d$name[1], side = d$side[1], frac = d$frac[1],
    lo = min(d$mond), hi = max(d$mond), med = median(d$mond),
    n_seed = nrow(d), stringsAsFactors = FALSE)))
# Coloured by DATASET, not by side: dodging six series while colouring by a
# two-level variable made several datasets share a hue at arbitrary dodge
# positions, so no bar could be attributed to its dataset. Side is recoverable
# from the sign and from panels A/B, dataset identity was not recoverable at all.
env$name <- factor(env$name, levels = sort(unique(env$name)))
f8c <- ggplot(env, aes(factor(frac), med, colour = name, group = name)) +
  geom_hline(yintercept = 0, linetype = 3, colour = "grey50") +
  geom_linerange(aes(ymin = lo, ymax = hi), linewidth = 0.5,
                 position = position_dodge(width = 0.7)) +
  geom_point(size = 1.7, position = position_dodge(width = 0.7)) +
  scale_ds_colour() +
  labs(x = "calibration fraction retained",
       y = "Mondrian coverage improvement", colour = NULL) +
  guides(colour = guide_legend(nrow = 2)) +
  theme_paper() + theme(legend.position = "bottom")

# ---- panel D: frozen cross-sectional cut the sweep fails to reproduce ------
xs <- do.call(rbind, lapply(DIA$rows, function(r) data.frame(
  cal  = num(g(r, "uncbin_cal_median")),
  mond = num(g(r, "mondrian_improvement_med")),
  stringsAsFactors = FALSE)))
xs <- xs[is.finite(xs$cal) & is.finite(xs$mond), ]
rho_xs <- suppressWarnings(cor(xs$cal, xs$mond, method = "spearman"))
# threshold read from the frozen diagnostic, never hardcoded
thr <- num(g(DIA$clean_threshold_separations[[1]], "threshold"))
f8d <- ggplot(xs, aes(cal, mond)) +
  geom_hline(yintercept = 0, linetype = 3, colour = "grey50") +
  geom_vline(xintercept = thr, linetype = 2, colour = "grey40") +
  annotate("text", x = thr, y = Inf, label = paste0("frozen cut = ", thr),
           hjust = 1.1, vjust = 1.5, size = 3.5, colour = "black",
           family = PAPER_FONT) +
  geom_point(size = 2.3, colour = okabe_ito[4]) +
  geom_smooth(method = "lm", se = TRUE, colour = okabe_ito[1], linewidth = 0.6) +
  scale_x_log10() +
  labs(x = "per-bin calibration fold size (log)",
       y = "Mondrian coverage improvement") +
  theme_paper()

f8 <- (f8a | f8b) / (f8c | f8d) + plot_annotation(tag_levels = "A") &
  paper_tag_theme
save_fig(f8, file.path(SDIR, "F8_calsize_planning"), w = 6.5, h = 5.2)

# ---- counts printed for every panel (provenance self-check) ----------------
vh <- PLAN$shape_verdict[[paste0(PRIMARY, "/helps")]]
vt <- PLAN$shape_verdict[[paste0(PRIMARY, "/hurts")]]
cat("F8 panel A (helps, lightgbm): n series=",
    length(unique(agg_med$name[agg_med$side == "helps"])),
    " n points=", sum(agg_med$side == "helps"),
    " median_rho(all arms)=", num(g(vh, "spearman_rho_mass_median")), "\n")
cat("F8 panel B (hurts, lightgbm): n series=",
    length(unique(agg_med$name[agg_med$side == "hurts"])),
    " n points=", sum(agg_med$side == "hurts"),
    " median_rho(all arms)=", num(g(vt, "spearman_rho_mass_median")), "\n")
# Which series actually traversed a mass range, and which cells are definitional
# zeros: both drive what A/B are allowed to claim, so both are printed.
cat("F8 A/B mass span (max/min per dataset, >=3x gets a line):\n")
for (n in names(span)) cat("   ", n, "=", round(span[[n]], 2),
    if (span[[n]] >= 3) "(line)" else "(points only: mass pinned)", "\n")
cat("F8 A/B inert cells (Mondrian == split conformal by construction):",
    sum(agg_med$inert), "of", nrow(agg_med),
    if (sum(agg_med$inert)) paste0("[", paste(agg_med$name[agg_med$inert],
      agg_med$frac[agg_med$inert], sep = "@", collapse = ", "), "]") else "", "\n")
cat("F8 panel C (envelope): n dataset x frac cells=", nrow(env),
    " seeds per cell=", paste(sort(unique(env$n_seed)), collapse = "/"), "\n")
cat("F8 panel D (frozen cross-section): n rows=", nrow(xs),
    " rho=", round(rho_xs, 3), " threshold=", thr, "\n")
cat("F8 source: experiments/calsize_planning_2026-08-01/results.json",
    "+ experiments/results/nd1_s2_p4_calsize_diag_reconciled.json\n")
