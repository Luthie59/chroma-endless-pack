package fr.citadelle.messages;

import org.bukkit.Bukkit;
import org.bukkit.Color;
import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.NamespacedKey;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.World;
import org.bukkit.boss.BarColor;
import org.bukkit.boss.BarStyle;
import org.bukkit.boss.BossBar;
import org.bukkit.entity.Display;
import org.bukkit.entity.ItemDisplay;
import org.bukkit.entity.Player;
import org.bukkit.entity.TextDisplay;
import org.bukkit.inventory.ItemStack;
import org.bukkit.inventory.meta.ItemMeta;
import org.bukkit.util.Transformation;
import org.joml.Quaternionf;
import org.joml.Vector3f;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
import java.util.function.Function;

/** Display entities (vortex + label), particles and per-player boss bars of the rift. */
final class RiftVisuals {

    static final String TAG = "citadelle_faille";
    private static final Particle.DustOptions PURPLE = new Particle.DustOptions(Color.fromRGB(0x9B4DFF), 1.4f);
    private static final Particle.DustOptions GOLD = new Particle.DustOptions(Color.fromRGB(0xF6C850), 1.2f);
    private static final int SPIN_TICKS = 10;
    private static final double BEAM_HEIGHT = 40;

    private ItemDisplay outer, inner;
    private TextDisplay label;
    private float angle;
    private final Map<UUID, BossBar> bars = new HashMap<>();

    void spawn(Location center) {
        World w = center.getWorld();
        outer = vortex(w, center.clone().add(0, 3.2, 0), 4.5f);
        inner = vortex(w, center.clone().add(0, 3.2, 0), 2.6f);
        label = w.spawn(center.clone().add(0, 7.2, 0), TextDisplay.class, t -> {
            t.setPersistent(false);
            t.addScoreboardTag(TAG);
            t.setBillboard(Display.Billboard.CENTER);
            t.setBackgroundColor(Color.fromARGB(150, 10, 14, 32));
            t.setViewRange(3f);
            t.setText("§5§l⌛ FAILLE TEMPORELLE ⌛");
        });
    }

    private static ItemDisplay vortex(World w, Location at, float scale) {
        return w.spawn(at, ItemDisplay.class, d -> {
            ItemStack item = new ItemStack(Material.PAPER);
            ItemMeta meta = item.getItemMeta();
            if (meta != null) {
                meta.setItemModel(new NamespacedKey("chroma", "vortex"));
                item.setItemMeta(meta);
            }
            d.setItemStack(item);
            d.setPersistent(false);
            d.addScoreboardTag(TAG);
            d.setBillboard(Display.Billboard.VERTICAL);
            d.setBrightness(new Display.Brightness(15, 15));
            d.setViewRange(4f);
            d.setGlowing(true);
            d.setGlowColorOverride(Color.fromRGB(0x9B4DFF));
            d.setTransformation(new Transformation(new Vector3f(), new Quaternionf(), new Vector3f(scale), new Quaternionf()));
        });
    }

    void setLabel(String text) {
        if (label != null && label.isValid()) label.setText(text);
    }

    /** called every 2 ticks. */
    void animate(Location center, int tick, double radius, boolean active) {
        World w = center.getWorld();
        if (w == null) return;
        if (tick % SPIN_TICKS == 0) {
            angle += active ? 0.9f : 0.45f;
            spin(outer, angle);
            spin(inner, -angle * 1.6f);
        }
        int points = 36;
        double phase = tick * 0.08;
        for (int i = 0; i < points; i++) {
            double a = phase + i * Math.PI * 2 / points;
            Location p = center.clone().add(Math.cos(a) * radius, 0.15, Math.sin(a) * radius);
            w.spawnParticle(Particle.DUST, p, 1, 0, 0, 0, 0, i % 3 == 0 ? GOLD : PURPLE);
        }
        Location core = center.clone().add(0, 3.2, 0);
        w.spawnParticle(Particle.REVERSE_PORTAL, core, active ? 14 : 6, 0.8, 0.8, 0.8, 0.05);
        if (tick % 10 == 0) {
            for (double y = 6; y < BEAM_HEIGHT; y += 2.5) {
                w.spawnParticle(Particle.END_ROD, center.clone().add(0, y, 0), 1, 0.05, 0.3, 0.05, 0, null, true);
            }
            w.spawnParticle(Particle.DUST, center.clone().add(0, BEAM_HEIGHT, 0), 6, 0.4, 0.4, 0.4, 0, PURPLE, true);
        }
        if (tick % 80 == 0) w.playSound(core, Sound.BLOCK_PORTAL_AMBIENT, 1.2f, 0.6f);
    }

    private static void spin(ItemDisplay d, float a) {
        if (d == null || !d.isValid()) return;
        Transformation t = d.getTransformation();
        d.setInterpolationDelay(0);
        d.setInterpolationDuration(SPIN_TICKS);
        d.setTransformation(new Transformation(t.getTranslation(), new Quaternionf().rotateZ(a), t.getScale(), t.getRightRotation()));
    }

    void updateBars(Function<Player, String> title, double progress, BarColor color) {
        for (Player p : Bukkit.getOnlinePlayers()) {
            BossBar bar = bars.computeIfAbsent(p.getUniqueId(), id -> {
                BossBar b = Bukkit.createBossBar("", BarColor.PURPLE, BarStyle.SEGMENTED_10);
                b.addPlayer(p);
                return b;
            });
            if (!bar.getPlayers().contains(p)) bar.addPlayer(p);
            bar.setTitle(title.apply(p));
            bar.setColor(color);
            bar.setProgress(Math.max(0, Math.min(1, progress)));
        }
    }

    void removeBar(UUID id) {
        BossBar bar = bars.remove(id);
        if (bar != null) bar.removeAll();
    }

    void remove() {
        for (Display d : new Display[]{outer, inner, label}) {
            if (d != null && d.isValid()) d.remove();
        }
        outer = inner = null;
        label = null;
        bars.values().forEach(BossBar::removeAll);
        bars.clear();
    }
}
