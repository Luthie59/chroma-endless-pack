package fr.citadelle.messages;

import org.bukkit.Bukkit;
import org.bukkit.Color;
import org.bukkit.Location;
import org.bukkit.World;
import org.bukkit.configuration.ConfigurationSection;
import org.bukkit.configuration.file.YamlConfiguration;
import org.bukkit.entity.Display;
import org.bukkit.entity.Entity;
import org.bukkit.entity.TextDisplay;
import org.bukkit.event.EventHandler;
import org.bukkit.event.EventPriority;
import org.bukkit.event.Listener;
import org.bukkit.event.entity.EntitySpawnEvent;
import org.bukkit.event.world.ChunkLoadEvent;
import org.bukkit.util.Transformation;
import org.joml.Quaternionf;
import org.joml.Vector3f;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;

/**
 * "Les Grandes Maisons": faction ranking by prestige = power*wP + land*wL + rift wins*wF,
 * shown on a hologram at the spawn (non-persistent TextDisplay, respawned with its chunk) and in chat.
 * Rift wins are kept in maisons.yml.
 */
final class HousesBoard implements Listener {

    record Ranked(FactionBridge.House house, int wins, int prestige) { }

    static final String TAG = "citadelle_maisons";
    private static final int DEFAULT_TOP = 5;
    private static final int LINE_WIDTH = 320;
    private static final String[] MEDALS = {"§6§l①", "§f§l②", "§c§l③", "§7④", "§7⑤", "§7⑥", "§7⑦", "§7⑧", "§7⑨", "§7⑩"};

    private final CitadelleMessages plugin;
    private final FactionBridge factions;
    private final File store;
    private final YamlConfiguration wins;
    private TextDisplay display;

    HousesBoard(CitadelleMessages plugin, FactionBridge factions) {
        this.plugin = plugin;
        this.factions = factions;
        this.store = new File(plugin.getDataFolder(), "maisons.yml");
        this.wins = YamlConfiguration.loadConfiguration(store);
        Bukkit.getScheduler().runTaskLater(plugin, this::respawn, 40L);
        Bukkit.getScheduler().runTaskTimer(plugin, this::watchdog, 100L, 100L);
        Bukkit.getScheduler().runTaskTimer(plugin, this::refresh, 100L, Math.max(10, cfg().getInt("refresh-seconds", 60)) * 20L);
    }

    private ConfigurationSection cfg() {
        ConfigurationSection s = plugin.getConfig().getConfigurationSection("maisons");
        return s != null ? s : plugin.getConfig().createSection("maisons");
    }

    // ------------------------------------------------------------------ ranking

    void recordWin(FactionBridge.Team team) {
        if (team.solo()) return;
        String key = "victoires." + team.key().replace(':', '_');
        wins.set(key, wins.getInt(key) + 1);
        try {
            wins.save(store);
        } catch (IOException e) {
            plugin.getLogger().warning("Victoire de faille non sauvegardée : " + e.getMessage());
        }
        refresh();
    }

    void resetWins() {
        wins.set("victoires", null);
        try {
            wins.save(store);
        } catch (IOException e) {
            plugin.getLogger().warning("maisons.yml non sauvegardé : " + e.getMessage());
        }
        refresh();
    }

    private int weight(String key, int def) {
        ConfigurationSection w = cfg().getConfigurationSection("prestige");
        return w != null ? w.getInt(key, def) : def;
    }

    String formula() {
        return "§8Prestige = " + weight("power", 1) + " × power + " + weight("terres", 2) + " × terres + "
                + weight("failles", 25) + " × failles gagnées";
    }

    List<Ranked> ranking() {
        int wp = weight("power", 1), wl = weight("terres", 2), wf = weight("failles", 25);
        List<Ranked> out = new ArrayList<>();
        for (FactionBridge.House h : factions.houses()) {
            int v = wins.getInt("victoires.f_" + h.id());
            out.add(new Ranked(h, v, h.power() * wp + h.land() * wl + v * wf));
        }
        out.sort(Comparator.comparingInt(Ranked::prestige).reversed().thenComparing(r -> r.house().name(), String.CASE_INSENSITIVE_ORDER));
        return out;
    }

    List<String> lines(int top) {
        List<Ranked> r = ranking();
        List<String> out = new ArrayList<>();
        if (r.isEmpty()) {
            out.add("§7Aucune maison n'a encore été fondée…");
            out.add("§8/f create <nom> pour écrire l'histoire");
            return out;
        }
        for (int i = 0; i < Math.min(top, r.size()); i++) {
            Ranked x = r.get(i);
            String name = (i == 0 ? "§e§l" : "§e") + x.house().name();
            out.add(MEDALS[Math.min(i, MEDALS.length - 1)] + " " + name + " §8— §d✦ " + x.prestige() + " §7prestige");
            out.add("§8⚡ §7" + x.house().power() + " power  §8⚑ §7" + x.house().land() + " terres  §8☺ §7"
                    + x.house().members() + " membres  §8⌛ §7" + x.wins() + (x.wins() > 1 ? " failles" : " faille"));
        }
        return out;
    }

    private String text() {
        List<String> body = lines(Math.max(1, Math.min(10, cfg().getInt("top", DEFAULT_TOP))));
        StringBuilder sb = new StringBuilder("§6§l⚜ LES GRANDES MAISONS ⚜\n§7Les factions les plus prestigieuses de la Citadelle\n§8━━━━━━━━━━━━━━━━━━━━━━━━\n");
        for (String l : body) sb.append(l).append('\n');
        sb.append("§8━━━━━━━━━━━━━━━━━━━━━━━━\n").append(formula());
        return sb.toString();
    }

    void refresh() {
        if (display != null && display.isValid()) display.setText(text());
    }

    // ------------------------------------------------------------------ hologram

    private Location saved() {
        ConfigurationSection s = cfg().getConfigurationSection("holo");
        if (s == null) return null;
        World w = Bukkit.getWorld(s.getString("world", "world"));
        if (w == null) return null;
        return new Location(w, s.getDouble("x"), s.getDouble("y"), s.getDouble("z"), (float) s.getDouble("yaw"), 0f);
    }

    void place(Location at) {
        plugin.getConfig().set("maisons.holo.world", at.getWorld().getName());
        plugin.getConfig().set("maisons.holo.x", at.getBlockX() + 0.5);
        plugin.getConfig().set("maisons.holo.y", at.getY() + 2.6);
        plugin.getConfig().set("maisons.holo.z", at.getBlockZ() + 0.5);
        plugin.getConfig().set("maisons.holo.yaw", (Math.round(at.getYaw() / 45f) * 45f + 180f) % 360f);   // faces the player who placed it
        plugin.saveConfig();
        respawn();
    }

    void removeForGood() {
        despawn();
        plugin.getConfig().set("maisons.holo", null);
        plugin.saveConfig();
    }

    void respawn() {
        despawn();
        Location at = saved();
        if (at == null) return;
        for (Entity e : at.getChunk().getEntities()) {
            if (e.getScoreboardTags().contains(TAG)) e.remove();
        }
        display = at.getWorld().spawn(at, TextDisplay.class, t -> {
            t.setPersistent(false);
            t.addScoreboardTag(TAG);
            t.setBillboard(Display.Billboard.FIXED);
            t.setAlignment(TextDisplay.TextAlignment.CENTER);
            t.setLineWidth(LINE_WIDTH);
            t.setShadowed(true);
            t.setBackgroundColor(Color.fromARGB(190, 10, 14, 32));
            t.setBrightness(new Display.Brightness(15, 15));
            t.setViewRange(1.5f);
            t.setTransformation(new Transformation(new Vector3f(), new Quaternionf(), new Vector3f(1.25f), new Quaternionf()));
            t.setText(text());
        });
    }

    /** every few seconds: if our chunk is loaded but the entity is gone (chunk reloaded early, removed…), respawn. */
    private void watchdog() {
        Location at = saved();
        if (at == null || (display != null && display.isValid())) return;
        if (at.getWorld().isChunkLoaded(at.getBlockX() >> 4, at.getBlockZ() >> 4)) respawn();
    }

    void despawn() {
        if (display != null && display.isValid()) display.remove();
        display = null;
    }

    /** the spawn's WorldGuard region may cancel entity spawns: let our own hologram through. */
    @EventHandler(priority = EventPriority.MONITOR)
    public void onSpawn(EntitySpawnEvent event) {
        if (event.isCancelled() && event.getEntity().getScoreboardTags().contains(TAG)) event.setCancelled(false);
    }

    @EventHandler
    public void onChunkLoad(ChunkLoadEvent event) {
        Location at = saved();
        if (at == null || (display != null && display.isValid())) return;
        if (event.getWorld().equals(at.getWorld()) && event.getChunk().getX() == at.getBlockX() >> 4
                && event.getChunk().getZ() == at.getBlockZ() >> 4) {
            Bukkit.getScheduler().runTask(plugin, () -> { if (display == null || !display.isValid()) respawn(); });
        }
    }
}
