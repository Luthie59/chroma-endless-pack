package fr.citadelle.messages;

import org.bukkit.Bukkit;
import org.bukkit.GameMode;
import org.bukkit.Location;
import org.bukkit.Sound;
import org.bukkit.World;
import org.bukkit.boss.BarColor;
import org.bukkit.entity.Player;
import org.bukkit.event.EventHandler;
import org.bukkit.event.Listener;
import org.bukkit.event.player.PlayerQuitEvent;
import org.bukkit.scheduler.BukkitTask;

import java.time.LocalTime;
import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;
import java.util.Comparator;
import java.util.List;
import java.util.HashMap;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Optional;
import java.util.Random;
import java.util.UUID;

/**
 * "Faille temporelle": a KOTH-like event. WARMUP (coordinates announced) then ACTIVE: the side alone
 * in the zone accumulates control; first to capture-seconds (or the leader at timeout) wins the chest.
 */
final class TimeRift implements Listener {

    enum Phase { IDLE, WARMUP, ACTIVE }

    private enum Control { FREE, HELD, CONTESTED }

    private static final DateTimeFormatter HHMM = DateTimeFormatter.ofPattern("HH:mm");
    private static final double ZONE_HEIGHT = 6;
    private static final double MOB_PLAYER_RANGE = 48;
    private static final int AUTO_CHECK_TICKS = 20 * 20;
    private static final int MIN_REWARD_SECONDS = 30;
    private static final int TICKET_RADIUS = 1;

    private final CitadelleMessages plugin;
    private final FactionBridge factions;
    private final RiftVisuals visuals = new RiftVisuals();
    private final RiftMobs mobs;
    private final RiftLoot loot;
    private final Random rnd = new Random();

    private RiftConfig cfg;
    private Phase phase = Phase.IDLE;
    private Location center;
    private int countdown, elapsed, tick;
    private Control control = Control.FREE;
    private FactionBridge.Team holder;
    private final Map<String, Integer> progress = new HashMap<>();
    private final Map<String, FactionBridge.Team> teams = new HashMap<>();
    /** seconds spent in the zone, per team then per player (only real contributors are rewarded). */
    private final Map<String, Map<UUID, Integer>> participants = new HashMap<>();
    private BukkitTask secondTask, fastTask;
    private String lastAutoMinute = "";

    private final java.util.function.Consumer<FactionBridge.Team> onWin;

    TimeRift(CitadelleMessages plugin, Chronon chronon, FactionBridge factions, java.util.function.Consumer<FactionBridge.Team> onWin) {
        this.plugin = plugin;
        this.factions = factions;
        this.onWin = onWin;
        this.mobs = new RiftMobs(chronon);
        this.loot = new RiftLoot(plugin, factions, chronon);
        reload();
        Bukkit.getPluginManager().registerEvents(this, plugin);
        Bukkit.getPluginManager().registerEvents(mobs, plugin);
        Bukkit.getPluginManager().registerEvents(loot, plugin);
        Bukkit.getScheduler().runTaskTimer(plugin, this::autoCheck, AUTO_CHECK_TICKS, AUTO_CHECK_TICKS);
    }

    void reload() {
        org.bukkit.configuration.ConfigurationSection s = plugin.getConfig().getConfigurationSection("faille");
        cfg = RiftConfig.load(s != null ? s : plugin.getConfig().createSection("faille"));
    }

    Phase phase() { return phase; }
    Location center() { return center == null ? null : center.clone(); }
    RiftConfig config() { return cfg; }

    // ------------------------------------------------------------------ lifecycle

    /** @return null on success, otherwise the reason (French) why it could not start. */
    String start(Location forced) {
        if (phase != Phase.IDLE) return "une faille est déjà ouverte";
        World world = forced != null ? forced.getWorld() : Bukkit.getWorld(cfg.world());
        if (world == null) return "monde « " + cfg.world() + " » introuvable";
        Location at = forced != null ? forced.getBlock().getLocation().add(0.5, 0, 0.5)
                : RiftLocator.find(world, cfg, factions, rnd);
        if (at == null) return "aucun emplacement libre trouvé (claims, eau…)";
        center = at;
        tickets(true);
        progress.clear(); teams.clear(); participants.clear();
        holder = null; control = Control.FREE; elapsed = 0; tick = 0;
        countdown = cfg.warmupSeconds();
        phase = Phase.WARMUP;
        visuals.spawn(center);
        announceOpening();
        secondTask = Bukkit.getScheduler().runTaskTimer(plugin, this::everySecond, 20L, 20L);
        fastTask = Bukkit.getScheduler().runTaskTimer(plugin, () -> { tick += 2; visuals.animate(center, tick, cfg.radius(), phase == Phase.ACTIVE); }, 2L, 2L);
        return null;
    }

    void stop(boolean announce) {
        if (phase == Phase.IDLE) return;
        if (announce) broadcast("§5⌛ §7La faille temporelle s'est refermée… §8(arrêtée par le staff)");
        end();
    }

    void shutdown() {
        end();
        loot.remove();
    }

    private void end() {
        if (secondTask != null) secondTask.cancel();
        if (fastTask != null) fastTask.cancel();
        secondTask = fastTask = null;
        visuals.remove();
        mobs.clear();
        if (center != null && center.getWorld() != null) tickets(false);
        phase = Phase.IDLE;
    }

    /** keep the 3x3 chunks around the rift loaded (zone, visuals, mobs) while it lives. */
    private void tickets(boolean add) {
        World w = center.getWorld();
        int cx = center.getBlockX() >> 4, cz = center.getBlockZ() >> 4;
        for (int dx = -TICKET_RADIUS; dx <= TICKET_RADIUS; dx++) {
            for (int dz = -TICKET_RADIUS; dz <= TICKET_RADIUS; dz++) {
                if (add) w.getChunkAt(cx + dx, cz + dz).addPluginChunkTicket(plugin);
                else w.getChunkAt(cx + dx, cz + dz).removePluginChunkTicket(plugin);
            }
        }
    }

    // ------------------------------------------------------------------ ticking

    private void everySecond() {
        if (phase == Phase.WARMUP) {
            countdown--;
            if (countdown == 60 || countdown == 30 || countdown == 10) {
                broadcast("§5⌛ §7La faille s'ouvre dans §e" + countdown + " s §7en §fX " + center.getBlockX() + " §7/ §fZ " + center.getBlockZ());
            }
            if (countdown <= 0) activate();
        } else if (phase == Phase.ACTIVE) {
            elapsed++;
            capture();
            if (phase != Phase.ACTIVE) return;               // won during capture()
            if (elapsed % cfg.waveIntervalSeconds() == 0) wave();
            if (elapsed >= cfg.maxDurationSeconds()) timeout();
        }
        if (phase != Phase.IDLE) refreshHud();
    }

    private void activate() {
        phase = Phase.ACTIVE;
        mobs.spawnGuardian(center);
        wave();
        for (Player p : Bukkit.getOnlinePlayers()) {
            p.sendTitle("§5§l⌛ La faille est ouverte ⌛", "§7Tenez la zone §e" + fmt(cfg.captureSeconds()) + " §7pour la remporter !", 10, 60, 20);
            p.playSound(p.getLocation(), Sound.BLOCK_END_PORTAL_SPAWN, 0.6f, 1.2f);
        }
        broadcast("§5⌛ §dLa faille temporelle est ouverte ! §7Le §4Gardien de la Faille §7en est sorti…");
    }

    private void wave() {
        if (cfg.maxMobs() <= 0) return;
        long near = center.getWorld().getPlayers().stream()
                .filter(p -> p.getLocation().distanceSquared(center) < MOB_PLAYER_RANGE * MOB_PLAYER_RANGE).count();
        if (near == 0) return;
        int room = cfg.maxMobs() - mobs.aliveCount();
        if (room > 0) mobs.spawnWave(center, (int) Math.min(room, 3 + near));
    }

    private void capture() {
        Map<String, FactionBridge.Team> present = new LinkedHashMap<>();
        for (Player p : center.getWorld().getPlayers()) {
            if (!inZone(p)) continue;
            FactionBridge.Team t = factions.teamOf(p);
            present.putIfAbsent(t.key(), t);
            teams.put(t.key(), t);
            participants.computeIfAbsent(t.key(), k -> new HashMap<>()).merge(p.getUniqueId(), 1, Integer::sum);
        }
        if (present.size() > 1) { control = Control.CONTESTED; return; }
        if (present.isEmpty()) { control = Control.FREE; return; }
        FactionBridge.Team t = present.values().iterator().next();
        if (holder == null || !holder.key().equals(t.key()) || control != Control.HELD) {
            broadcast("§5⌛ " + label(t) + " §7prend le contrôle de la faille !");
        }
        holder = t;
        control = Control.HELD;
        if (progress.merge(t.key(), 1, Integer::sum) >= cfg.captureSeconds()) win(t);
    }

    private boolean inZone(Player p) {
        if (p.isDead() || (p.getGameMode() != GameMode.SURVIVAL && p.getGameMode() != GameMode.ADVENTURE)) return false;
        if (isVanished(p)) return false;
        Location l = p.getLocation();
        double dx = l.getX() - center.getX(), dz = l.getZ() - center.getZ();
        return dx * dx + dz * dz <= cfg.radius() * cfg.radius() && Math.abs(l.getY() - center.getY()) <= ZONE_HEIGHT;
    }

    /** Essentials / Staff++ keep a "vanished" metadata on everyone: only a true value means hidden. */
    private static boolean isVanished(Player p) {
        return p.getMetadata("vanished").stream().anyMatch(org.bukkit.metadata.MetadataValue::asBoolean);
    }

    private void timeout() {
        Optional<Map.Entry<String, Integer>> best = progress.entrySet().stream().max(Comparator.comparingInt(Map.Entry::getValue));
        if (best.isPresent() && best.get().getValue() > 0) {
            win(teams.get(best.get().getKey()));
        } else {
            broadcast("§5⌛ §7Personne n'a tenu la faille… elle s'effondre sur elle-même.");
            end();
        }
    }

    private void win(FactionBridge.Team t) {
        Location c = center.clone();
        int needed = Math.min(MIN_REWARD_SECONDS, cfg.captureSeconds() / 3);
        List<Player> rewarded = new ArrayList<>();
        for (Map.Entry<UUID, Integer> e : participants.getOrDefault(t.key(), Map.of()).entrySet()) {
            Player p = Bukkit.getPlayer(e.getKey());
            if (p != null && (e.getValue() >= needed || inZone(p))) rewarded.add(p);
        }
        List<Player> runnersUp = new ArrayList<>();
        for (Map.Entry<String, Map<UUID, Integer>> team : participants.entrySet()) {
            if (team.getKey().equals(t.key())) continue;
            for (Map.Entry<UUID, Integer> e : team.getValue().entrySet()) {
                Player p = Bukkit.getPlayer(e.getKey());
                if (p != null && e.getValue() >= needed) runnersUp.add(p);
            }
        }
        end();                                   // first: a failing reward command must never replay the win
        for (Player p : Bukkit.getOnlinePlayers()) {
            p.sendTitle("§6§l✦ " + t.name() + " ✦", "§7remporte la faille temporelle !", 10, 70, 20);
            p.playSound(p.getLocation(), Sound.UI_TOAST_CHALLENGE_COMPLETE, 0.8f, 1f);
        }
        boolean chest = loot.place(c, t, cfg);
        try {
            onWin.accept(t);
        } catch (RuntimeException ex) {
            plugin.getLogger().warning("Victoire non enregistrée au classement : " + ex);
        }
        broadcast("§5⌛ " + label(t) + " §6remporte la faille temporelle !"
                + (chest ? " §7Le §6coffre du temps §7est apparu en son cœur." : ""));
        for (Player p : rewarded) {
            for (String cmd : cfg.rewardCommands()) run(cmd, p, t);
            p.sendMessage("§6✦ §7Récompense de la faille reçue !");
        }
        for (Player p : runnersUp) {
            for (String cmd : cfg.participationCommands()) run(cmd, p, t);
            p.sendMessage("§5⌛ §7Tu t'es battu pour la faille : récompense de participation reçue.");
        }
    }

    private void run(String cmd, Player p, FactionBridge.Team t) {
        String line = cmd.replace("{player}", p.getName()).replace("{faction}", t.name());
        try {
            Bukkit.dispatchCommand(Bukkit.getConsoleSender(), line);
        } catch (RuntimeException ex) {
            plugin.getLogger().warning("Récompense de faille échouée (" + line + ") : " + ex);
        }
    }

    // ------------------------------------------------------------------ HUD

    private void refreshHud() {
        String where = "§fX " + center.getBlockX() + " §7/ §fZ " + center.getBlockZ();
        String head;
        double bar;
        BarColor color = BarColor.PURPLE;
        if (phase == Phase.WARMUP) {
            head = "§d⌛ Faille temporelle §8» " + where + " §8» §7ouverture §e" + fmt(countdown);
            bar = 1 - (double) countdown / cfg.warmupSeconds();
            visuals.setLabel("§5§l⌛ FAILLE TEMPORELLE ⌛\n§7Ouverture dans §e" + fmt(countdown));
        } else {
            int left = cfg.maxDurationSeconds() - elapsed;
            if (control == Control.CONTESTED) { head = "§c⚔ Faille contestée ! §8» " + where; color = BarColor.RED; }
            else if (control == Control.HELD) { head = label(holder) + " §7tient la faille §8» §e" + pct(holder) + "%"; color = BarColor.YELLOW; }
            else head = "§d⌛ Faille libre §8» " + where + " §8» §7fin §e" + fmt(left);
            bar = holder == null ? 0 : (double) progress.getOrDefault(holder.key(), 0) / cfg.captureSeconds();
            visuals.setLabel("§5§l⌛ FAILLE TEMPORELLE ⌛\n" + (holder == null ? "§7Personne ne la tient" : label(holder) + " §e" + pct(holder) + "%")
                    + "\n§7Fin dans §e" + fmt(left));
        }
        final String h = head;
        visuals.updateBars(p -> h + distance(p), bar, color);
    }

    private String distance(Player p) {
        if (p.getWorld() != center.getWorld()) return "";
        return " §8(" + (int) p.getLocation().distance(center) + " m)";
    }

    private int pct(FactionBridge.Team t) {
        return (int) Math.min(100, 100.0 * progress.getOrDefault(t.key(), 0) / cfg.captureSeconds());
    }

    private static String label(FactionBridge.Team t) {
        return t.solo() ? "§e" + t.name() : "§bla faction §l" + t.name();
    }

    private static String fmt(int s) {
        return String.format("%d:%02d", Math.max(0, s) / 60, Math.max(0, s) % 60);
    }

    private void announceOpening() {
        String dir = RiftLocator.direction(center.getX(), center.getZ());
        int dist = (int) Math.hypot(center.getX(), center.getZ());
        broadcast("");
        broadcast("§5§l    ⌛ FAILLE TEMPORELLE ⌛");
        broadcast("§7    Une déchirure dans le temps apparaît en §fX " + center.getBlockX() + " §7/ §fZ " + center.getBlockZ());
        broadcast("§7    (" + dir + " du spawn, à §e" + dist + " m§7). Ouverture dans §e" + fmt(countdown) + "§7.");
        broadcast("§7    Tenez-la §e" + fmt(cfg.captureSeconds()) + " §7pour gagner le §6coffre du temps§7 !");
        broadcast("");
        for (Player p : Bukkit.getOnlinePlayers()) {
            p.sendTitle("§5§l⌛ Faille temporelle ⌛", "§fX " + center.getBlockX() + " §7/ §fZ " + center.getBlockZ() + " §8— §7" + dir, 10, 70, 20);
            p.playSound(p.getLocation(), Sound.BLOCK_BEACON_POWER_SELECT, 0.8f, 0.6f);
        }
    }

    private static void broadcast(String msg) {
        Bukkit.broadcastMessage(msg);
    }

    // ------------------------------------------------------------------ schedule

    private void autoCheck() {
        if (!cfg.enabled() || !cfg.auto() || phase != Phase.IDLE) return;
        String now = ZonedDateTime.now(cfg.zone()).format(HHMM);
        if (now.equals(lastAutoMinute) || !cfg.times().contains(now)) return;
        lastAutoMinute = now;
        if (Bukkit.getOnlinePlayers().size() < cfg.minPlayers()) {
            plugin.getLogger().info("Faille de " + now + " annulée : pas assez de joueurs.");
            return;
        }
        String err = start(null);
        if (err != null) plugin.getLogger().warning("Faille automatique impossible : " + err);
    }

    /** next scheduled opening as "HH:mm", or null. */
    String nextTime() {
        if (!cfg.enabled() || !cfg.auto() || cfg.times().isEmpty()) return null;
        LocalTime now = ZonedDateTime.now(cfg.zone()).toLocalTime();
        return cfg.times().stream().sorted()
                .filter(t -> { try { return LocalTime.parse(t, HHMM).isAfter(now); } catch (RuntimeException e) { return false; } })
                .findFirst().orElse(cfg.times().stream().sorted().findFirst().orElse(null));
    }

    @EventHandler
    public void onQuit(PlayerQuitEvent event) {
        visuals.removeBar(event.getPlayer().getUniqueId());
    }
}
