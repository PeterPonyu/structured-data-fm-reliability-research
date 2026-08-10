# p4_figs_expansions.R -- expand F1-F6 from single/dual panels to 4 panels.
# Reads ONLY frozen on-disk result JSONs; no hardcoded numeric values.
# Run from any directory; paths are resolved relative to this file.
cargs <- commandArgs(trailingOnly = FALSE)
SDIR  <- dirname(normalizePath(sub("^--file=", "", cargs[grep("^--file=", cargs)][1])))
source(Sys.getenv("GGTHEME_R", file.path(SDIR, "ggtheme.R")))
library(patchwork)
ROOT <- Sys.getenv("ND1_RESULTS_ROOT",
        normalizePath(file.path(SDIR, "..", "..", "experiments", "results")))

# shared helpers
num  <- function(x) if (is.null(x)) NA_real_ else suppressWarnings(as.numeric(x))
g    <- function(r, k) if (!is.null(r[[k]])) r[[k]] else NA
vec  <- function(x) unlist(x, use.names = FALSE)

KEYED14 <- c("electricity","eucalyptus","adult","cylinder-bands","churn","Moneyball",
             "kick","black_friday","house_prices_nominal","colleges",
             "Airlines_DepDelay_10M","nyc-taxi-green-dec-2016","house_sales",
             "sf-police-incidents")

# ---- data loading ------------------------------------------------------------
S2KI  <- read_result(file.path(ROOT, "nd1_s2_lightgbm_mondrian.json"))
S2KE  <- read_result(file.path(ROOT, "nd1_s2_lightgbm_mondrian_keyexcluded.json"))
FM    <- read_result(file.path(ROOT, "nd1_tabicl_fm_arm_leakage_ablation.json"))
FMKE  <- read_result(file.path(ROOT, "nd1_tabicl_fm_arm_leakage_ablation_keyexcluded.json"))
DPT   <- read_result(file.path(ROOT, "nd1_tabdpt_fm_arm.json"))
GBMB  <- read_result(file.path(ROOT, "nd1_tuned_gbm_baseline.json"))
DIAKI <- read_result(file.path(ROOT, "nd1_s2_p4_calsize_diag_reconciled.json"))
DIAKE <- read_result(file.path(ROOT, "nd1_s2_p4_calsize_diag_reconciled_keyexcluded.json"))
AGG   <- read_result(file.path(ROOT, "split_repeats", "aggregate-split-repeats-2026-07-02.json"))
TS    <- read_result(file.path(ROOT, "p4_tableshift_result.json"))
PLAN  <- read_result(normalizePath(file.path(SDIR, "..", "..",
           "experiments", "calsize_planning_2026-08-01", "results.json")))

# helpers to build tidy data.frames from any of the arm JSONs
arm_df <- function(res_json, label = NULL) {
  rows <- lapply(res_json$results, function(r) {
    if (!is.null(r$status) && r$status == "ok" &&
        (is.null(KEYED14) || as.character(g(r,"name")) %in% KEYED14)) {
      data.frame(
        model         = label %||% as.character(g(r,"model")),
        name          = as.character(g(r,"name")),
        aurc_random   = num(g(r,"aurc_random")),
        aurc_grouped  = num(g(r,"aurc_grouped")),
        repair_grouped = num(g(r,"repair_ratio_grouped")),
        cov_grouped   = num(g(r, "conformal_cov_grouped") %||% g(r,"conformal_cov_grouped_split")),
        stringsAsFactors = FALSE)
    }
  })
  do.call(rbind, Filter(Negate(is.null), rows))
}
`%||%` <- function(a, b) if (!is.null(a)) a else b

# ============================================================================
# F1 (1→4): AURC dumbbell across model families
# A GBMs (key-included)   B TabICLv2   C TabDPT   D Tuned-GBM baseline
# ============================================================================
make_dumbbell <- function(d, ttl) {
  m <- rbind(
    data.frame(model=d$model, name=d$name, split="random",       aurc=d$aurc_random),
    data.frame(model=d$model, name=d$name, split="grouped/time", aurc=d$aurc_grouped))
  m$split <- factor(m$split, levels=c("random","grouped/time"))
  ggplot(m, aes(aurc, reorder(name, aurc))) +
    geom_line(aes(group=interaction(model,name)), colour="grey70", linewidth=0.4) +
    geom_point(aes(colour=split), size=1.8) +
    facet_wrap(~model) + scale_color_paper() + scale_x_log10() +
    labs(title=ttl, x="AURC (log; lower=better)", y=NULL, colour="split") +
    theme_paper() + theme(legend.position="bottom")
}
dfKI  <- arm_df(S2KI)
dfFM  <- arm_df(FM)
dfDPT <- arm_df(DPT)
dfGB  <- arm_df(GBMB)
f1 <- (make_dumbbell(dfKI,  "A  GBMs (key-included)") |
       make_dumbbell(dfFM,  "B  TabICLv2")) /
      (make_dumbbell(dfDPT, "C  TabDPT") |
       make_dumbbell(dfGB,  "D  Tuned GBM")) +
  plot_annotation(tag_levels="A") & paper_tag_theme
save_fig(f1, file.path(SDIR,"F1_aurc_random_vs_grouped"), w=6.5, h=4.73)
cat("F1: n rows GBM=",nrow(dfKI)," FM=",nrow(dfFM)," DPT=",nrow(dfDPT),
    " TunedGBM=",nrow(dfGB),"\n")

# ============================================================================
# F2 (1→4): repair ratio across families + key-excluded sensitivity
# A GBMs key-included   B FM arms   C GBMs key-excluded   D TabICLv2 key-excluded
# ============================================================================
make_repair <- function(d, ttl) {
  ggplot(d, aes(reorder(name, repair_grouped), repair_grouped, colour=model)) +
    geom_hline(yintercept=0, linetype=2, colour="grey60") +
    geom_point(size=2.2) + coord_flip() + scale_color_paper() +
    labs(title=ttl, x=NULL, y="grouped repair ratio") +
    theme_paper() + theme(legend.position="bottom")
}
dfKE  <- arm_df(S2KE)
dfFMKE <- arm_df(FMKE)
dfFM2 <- rbind(dfFM, dfDPT)  # TabICLv2 + TabDPT together in panel B
f2 <- (make_repair(dfKI,  "A  GBMs — key-included") |
       make_repair(dfFM2, "B  FM arms (TabICLv2 + TabDPT)")) /
      (make_repair(dfKE,  "C  GBMs — key-excluded") |
       make_repair(dfFMKE,"D  TabICLv2 — key-excluded")) +
  plot_annotation(tag_levels="A") & paper_tag_theme
save_fig(f2, file.path(SDIR,"F2_repair_ratio"), w=6.5, h=4.73)
cat("F2: KI=",nrow(dfKI)," FM2=",nrow(dfFM2)," KE=",nrow(dfKE)," FMKE=",nrow(dfFMKE),"\n")

# ============================================================================
# F3 (2→4): model agnosticism + key-excluded + tuned-GBM
# A XGB vs LGBM scatter (log-log — fixes linear axis collapse in prior version)
# B 4-family grouped coverage  C 4-family coverage key-excluded  D TunedGBM coverage
# ============================================================================
gbm_cov_ki <- do.call(rbind, lapply(S2KI$results, function(r) {
  cv <- num(g(r,"conformal_cov_grouped_split"))
  if (!is.na(cv)) data.frame(model=as.character(g(r,"model")),name=as.character(g(r,"name")),cov=cv)
}))
gbm_cov_ke <- do.call(rbind, lapply(S2KE$results, function(r) {
  cv <- num(g(r,"conformal_cov_grouped_split"))
  if (!is.na(cv)) data.frame(model=as.character(g(r,"model")),name=as.character(g(r,"name")),cov=cv)
}))
fm_cov_ki <- do.call(rbind, lapply(FM$results, function(r) {
  cv <- num(g(r,"conformal_cov_grouped"))
  if (!is.null(r$status) && r$status=="ok" && as.character(g(r,"name")) %in% KEYED14 && !is.na(cv))
    data.frame(model="TabICLv2", name=as.character(g(r,"name")), cov=cv)
}))
dpt_cov_ki <- do.call(rbind, lapply(DPT$results, function(r) {
  cv <- num(g(r,"conformal_cov_grouped"))
  if (!is.null(r$status) && r$status=="ok" && as.character(g(r,"name")) %in% KEYED14 && !is.na(cv))
    data.frame(model="TabDPT", name=as.character(g(r,"name")), cov=cv)
}))
fm_cov_ke <- do.call(rbind, lapply(FMKE$results, function(r) {
  cv <- num(g(r,"conformal_cov_grouped"))
  if (!is.null(r$status) && r$status=="ok" && as.character(g(r,"name")) %in% KEYED14 && !is.na(cv))
    data.frame(model="TabICLv2", name=as.character(g(r,"name")), cov=cv)
}))
dpt_ke <- data.frame(model=character(),name=character(),cov=numeric())  # DPT KE not in scope
gbm_cov_gb <- do.call(rbind, lapply(GBMB$results, function(r) {
  cv <- num(g(r,"conformal_cov_grouped"))
  if (!is.null(r$status) && r$status=="ok" && !is.na(cv))
    data.frame(model=as.character(g(r,"model")),name=as.character(g(r,"name")),cov=cv)
}))
cov4_ki <- rbind(gbm_cov_ki, fm_cov_ki, dpt_cov_ki)
cov4_ke <- rbind(gbm_cov_ke, fm_cov_ke)
levs <- c("lightgbm","xgboost","TabICLv2","TabDPT")
cov4_ki$model <- factor(cov4_ki$model, levels=levs)
cov4_ke$model <- factor(cov4_ke$model, levels=levs[levs %in% cov4_ke$model])
# Panel A: XGB vs LGBM aurc_grouped scatter — LOG-LOG fixes the linear collapse
xs <- dfKI[dfKI$model=="xgboost",  c("name","aurc_grouped")]; names(xs)[2]<-"xgboost"
ls <- dfKI[dfKI$model=="lightgbm", c("name","aurc_grouped")]; names(ls)[2]<-"lightgbm"
w  <- merge(xs,ls,by="name")
pA3 <- ggplot(w, aes(xgboost,lightgbm,label=name)) +
  geom_abline(slope=1,intercept=0,linetype=2,colour="grey60") +
  geom_point(size=2.5,colour=okabe_ito[1]) +
  scale_x_log10() + scale_y_log10() +
  labs(x="grouped AURC — XGBoost (log)", y="grouped AURC — LightGBM (log)") + theme_paper()
make_cov_panel <- function(d, ttl) {
  ggplot(d, aes(reorder(name,cov),cov,colour=model,shape=model)) +
    geom_hline(yintercept=0.90,linetype=2,colour="grey50",linewidth=0.5) +
    geom_point(size=2.2,position=position_dodge(0.6)) +
    scale_color_paper() + scale_shape_manual(values=c(16,17,15,18)) +
    scale_y_continuous(limits=c(0.15,1.02),breaks=seq(0.2,1.0,0.2)) +
    coord_flip() +
    labs(title=ttl,x=NULL,y="grouped coverage (target 0.90)",colour=NULL,shape=NULL) +
    guides(colour=guide_legend(nrow=2),shape=guide_legend(nrow=2)) +
    theme_paper()+theme(legend.position="bottom")
}
f3 <- (free(pA3,type="panel") | make_cov_panel(cov4_ki,"B  4 families — key-included")) /
      (make_cov_panel(cov4_ke,"C  4 families — key-excluded") |
       make_cov_panel(gbm_cov_gb[gbm_cov_gb$name %in% KEYED14,],"D  Tuned GBM")) +
  plot_layout(heights=c(1,1.5)) + plot_annotation(tag_levels="A") & paper_tag_theme
save_fig(f3, file.path(SDIR,"F3_model_agnostic"), w=6.5, h=5.32)
cat("F3: scatter n=",nrow(w)," cov4_ki=",nrow(cov4_ki)," cov4_ke=",nrow(cov4_ke),
    " gbmb=",nrow(gbm_cov_gb),"\n")

# ============================================================================
# F4 (2→4): calsize diagnostic  A/B keep  C model-colored  D planning-curve
# ============================================================================
calsize_panel <- function(diag, ttl=NULL) {
  fr <- do.call(rbind, lapply(diag$rows, function(r) data.frame(
    cal=num(g(r,"uncbin_cal_median")), mond=num(g(r,"mondrian_improvement_med")),
    stringsAsFactors=FALSE)))
  fr <- fr[is.finite(fr$cal) & is.finite(fr$mond),]
  rho <- suppressWarnings(cor(fr$cal,fr$mond,method="spearman"))
  p <- ggplot(fr,aes(cal,mond)) +
    geom_hline(yintercept=0,linetype=3,colour="grey50") +
    geom_point(size=2.3,colour=okabe_ito[4]) +
    geom_smooth(method="lm",se=TRUE,colour=okabe_ito[1],linewidth=0.6) +
    scale_x_log10() +
    labs(x="per-bin cal fold size (log)", y="Mondrian coverage improvement",
         subtitle=if(!is.null(ttl)) sprintf("%s  Spearman rho=%.3f (n=%d)",ttl,rho,nrow(fr)) else NULL) +
    theme_paper()
  list(plot=p, rho=rho, n=nrow(fr))
}
f4a <- calsize_panel(DIAKI, "key-included")
f4b <- calsize_panel(DIAKE, "key-excluded")
# Panel C: both datasets + both models, colored by model — all 28 rows
fr_all <- do.call(rbind, lapply(DIAKI$rows, function(r) data.frame(
  cal=num(g(r,"uncbin_cal_median")), mond=num(g(r,"mondrian_improvement_med")),
  model=as.character(g(r,"model")), stringsAsFactors=FALSE)))
fr_all <- fr_all[is.finite(fr_all$cal) & is.finite(fr_all$mond),]
pC4 <- ggplot(fr_all,aes(cal,mond,colour=model)) +
  geom_hline(yintercept=0,linetype=3,colour="grey50") +
  geom_point(size=2.3) + scale_color_paper() + scale_x_log10() +
  labs(x="per-bin cal fold size (log)", y="Mondrian coverage improvement",
       subtitle=sprintf("model-colored  n=%d",nrow(fr_all)),colour=NULL) +
  theme_paper()+theme(legend.position="bottom")
# Panel D: designed within-dataset sweep summary — floor1 rule, LightGBM
plan_rows <- PLAN$rows
plan_lgb <- lapply(plan_rows, function(r) {
  if (as.character(g(r,"rule"))=="floor1" && as.character(g(r,"model"))=="lightgbm")
    data.frame(name=as.character(g(r,"name")), side=as.character(g(r,"side")),
               frac=num(g(r,"frac")), mass=num(g(r,"uncbin_cal_median")),
               mond=num(g(r,"mondrian_improvement_med")), stringsAsFactors=FALSE)
})
plan_df <- do.call(rbind, Filter(Negate(is.null), plan_lgb))
plan_agg <- aggregate(mond~name+side+frac, data=plan_df[,c("name","side","frac","mond")], FUN=median)
DS_ALL4 <- sort(unique(plan_agg$name))
DS_COL4 <- setNames(okabe_ito[seq_along(DS_ALL4)], DS_ALL4)
pD4 <- ggplot(plan_agg, aes(factor(frac), mond, colour=name, group=name)) +
  geom_hline(yintercept=0,linetype=3,colour="grey50") +
  geom_line(linewidth=0.5) + geom_point(size=1.8) +
  scale_colour_manual(values=DS_COL4) +
  facet_wrap(~side, ncol=2) +
  labs(x="cal fraction", y="Mondrian improvement",
       subtitle="within-dataset sweep (floor1, lgbm)", colour=NULL) +
  theme_paper()+theme(legend.position="bottom")
f4 <- (f4a$plot | f4b$plot) / (pC4 | pD4) +
  plot_annotation(tag_levels="A") & paper_tag_theme
save_fig(f4, file.path(SDIR,"F4_calsize_vs_mondrian"), w=6.5, h=5.32)
cat("F4: A n=",f4a$n," rho=",round(f4a$rho,3)," B n=",f4b$n," C n=",nrow(fr_all),
    " D n=",nrow(plan_agg),"\n")

# ============================================================================
# F5 (2→4): TableShift  A/B keep  C per-RAC1P group coverage  D gap random-OOD
# ============================================================================
df5 <- do.call(rbind, lapply(TS$results, function(r) {
  if (is.null(r$status) || r$status != "ok") return(NULL)
  grp <- r$grouped_coverage_per_RAC1P
  base <- data.frame(task=as.character(g(r,"task")), model=as.character(g(r,"model")),
    repair_ood=num(g(r,"repair_ood_med")), repair_lo=num(g(r,"repair_ood_ci")[[1]]),
    repair_hi=num(g(r,"repair_ood_ci")[[2]]),
    sub_gap=num(g(r,"grouped_coverage_gap_worst_minus_best")),
    sub_gap_lo=num(g(r,"grouped_coverage_gap_ci")[[1]]),
    sub_gap_hi=num(g(r,"grouped_coverage_gap_ci")[[2]]),
    gap_med=num(g(r,"coverage_gap_random_minus_ood_med")),
    gap_lo=num(g(r,"coverage_gap_random_minus_ood_ci")[[1]]),
    gap_hi=num(g(r,"coverage_gap_random_minus_ood_ci")[[2]]),
    stringsAsFactors=FALSE)
  base
}))
pA5 <- ggplot(df5, aes(reorder(task,repair_ood), repair_ood, colour=model)) +
  geom_hline(yintercept=0,linetype=2,colour="grey60") +
  geom_pointrange(aes(ymin=repair_lo,ymax=repair_hi),position=position_dodge(0.5),size=0.45) +
  coord_flip() + scale_color_paper() +
  labs(x=NULL, y="OOD repair ratio") + theme_paper()
pB5 <- ggplot(df5, aes(reorder(task,sub_gap), sub_gap, colour=model)) +
  geom_hline(yintercept=0,linetype=2,colour="grey60") +
  geom_pointrange(aes(ymin=sub_gap_lo,ymax=sub_gap_hi),position=position_dodge(0.5),size=0.45) +
  coord_flip() + scale_color_paper() +
  labs(x=NULL, y="RAC1P coverage gap\n(worst-best)") + theme_paper()
# Panel C: per-RAC1P group coverage (5 groups × 4 tasks × 2 models)
rac1p_rows <- lapply(TS$results, function(r) {
  if (is.null(r$status) || r$status != "ok") return(NULL)
  grp <- r$grouped_coverage_per_RAC1P
  if (is.null(grp) || length(grp)==0) return(NULL)
  do.call(rbind, lapply(names(grp), function(racid) data.frame(
    task=as.character(g(r,"task")), model=as.character(g(r,"model")),
    racid=racid, cov=num(grp[[racid]]), stringsAsFactors=FALSE)))
})
rac1p <- do.call(rbind, Filter(Negate(is.null), rac1p_rows))
pC5 <- ggplot(rac1p, aes(racid, cov, colour=model, group=model)) +
  geom_hline(yintercept=0.90, linetype=2, colour="grey50", linewidth=0.5) +
  geom_point(size=2.0, position=position_dodge(0.4)) +
  facet_wrap(~task, nrow=1) + scale_color_paper() +
  scale_y_continuous(limits=c(0.75,1.02), breaks=seq(0.8,1.0,0.1)) +
  labs(x="RAC1P group", y="conformal coverage (target 0.90)", colour=NULL) +
  theme_paper()+theme(legend.position="bottom")
# Panel D: coverage gap random-OOD with bootstrap CI
pD5 <- ggplot(df5, aes(reorder(task,gap_med), gap_med, colour=model)) +
  geom_hline(yintercept=0, linetype=2, colour="grey60") +
  geom_pointrange(aes(ymin=gap_lo,ymax=gap_hi), position=position_dodge(0.5), size=0.45) +
  coord_flip() + scale_color_paper() +
  labs(x=NULL, y="coverage gap (random − OOD)\n(>0 = OOD under-covers)") + theme_paper()
f5 <- (pA5 | pB5) / (pC5 | pD5) +
  plot_annotation(tag_levels="A") & paper_tag_theme
save_fig(f5, file.path(SDIR,"F5_tableshift"), w=6.5, h=4.73)
cat("F5: df5 rows=",nrow(df5)," RAC1P cells=",nrow(rac1p),"\n")

# ============================================================================
# F6 (1→4): split-realization fragility — all four arm combinations
# A LGBM-S2-keyIn   B XGB-S2-keyIn   C LGBM-S2-keyEx   D XGB-S1-keyIn
# All data in the aggregate split-repeats JSON; no recomputation.
# ============================================================================
MAJ <- num(g(AGG, "majority_threshold"))
mk_dist <- function(node, label) {
  data.frame(metric=label, count=as.integer(vec(node$per_k)), stringsAsFactors=FALSE)
}
frag_arm <- function(node) {
  d <- rbind(
    mk_dist(node$grouped_gap_count,   "grouped-gap"),
    mk_dist(node$repair_count,        "repair-beats-random"),
    mk_dist(node$aurc_degrade_count,  "AURC-degrade"),
    mk_dist(node$undercover_count,    "under-coverage"))
  d$metric <- factor(d$metric, levels=c("grouped-gap","AURC-degrade",
                                         "under-coverage","repair-beats-random"))
  d[is.finite(d$count) & d$count > 0, ]
}
make_frag_panel <- function(d, ttl) {
  ggplot(d, aes(count, fill=metric)) +
    geom_bar(position=position_dodge(preserve="single"), width=0.85) +
    geom_vline(xintercept=MAJ-0.5, linetype=2, colour="grey40") +
    annotate("text", x=MAJ-0.5, y=Inf, label=paste0("≥",MAJ), hjust=1.2,
             vjust=1.6, size=3.2, colour="black", family=PAPER_FONT) +
    scale_fill_paper() +
    scale_x_continuous(breaks=seq(0,14,2)) +
    labs(title=ttl, x="count (of 14 datasets)", y="split draws", fill=NULL) +
    guides(fill=guide_legend(nrow=2)) +
    theme_paper()+theme(legend.position="bottom")
}
d_lgb_ki  <- frag_arm(AGG$stage2$key_included$lightgbm)
d_xgb_ki  <- frag_arm(AGG$stage2$key_included$xgboost)
d_lgb_ke  <- frag_arm(AGG$stage2$key_excluded$lightgbm)
d_xgb_s1  <- frag_arm(AGG$stage1_xgboost$key_included)

f6 <- (make_frag_panel(d_lgb_ki, "A  LGBM — Stage-2 key-included") |
       make_frag_panel(d_xgb_ki, "B  XGB  — Stage-2 key-included")) /
      (make_frag_panel(d_lgb_ke, "C  LGBM — Stage-2 key-excluded") |
       make_frag_panel(d_xgb_s1, "D  XGB  — Stage-1 key-included")) +
  plot_annotation(tag_levels="A") & paper_tag_theme
save_fig(f6, file.path(SDIR,"F6_split_repeats_fragility"), w=6.5, h=4.14)
cat("F6: lgb_ki=",nrow(d_lgb_ki)," xgb_ki=",nrow(d_xgb_ki),
    " lgb_ke=",nrow(d_lgb_ke)," xgb_s1=",nrow(d_xgb_s1),"\n")
cat("All expansions done.\n")
