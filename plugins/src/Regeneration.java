package fr.citadelle.messages;

import org.bukkit.Color;
import org.bukkit.Location;
import org.bukkit.Particle;
import org.bukkit.Sound;
import org.bukkit.World;
import org.bukkit.configuration.ConfigurationSection;
import org.bukkit.entity.Player;
import org.bukkit.event.EventHandler;
import org.bukkit.event.EventPriority;
import org.bukkit.event.Listener;
import org.bukkit.event.entity.PlayerDeathEvent;
import org.bukkit.event.player.PlayerRespawnEvent;
import org.bukkit.potion.PotionEffect;
import org.bukkit.potion.PotionEffectType;
import org.bukkit.scheduler.BukkitRunnable;

import java.lang.reflect.Method;

/**
 * "Régénération" : golden burst where a player dies, themed death message,
 * and a rising golden spiral + title when they come back.
 */
final class Regeneration implements Listener {

    private static final Particle.DustOptions GOLD = new Particle.DustOptions(Color.fromRGB(0xF6C850), 1.3f);
    private static final Particle.DustOptions AMBER = new Particle.DustOptions(Color.fromRGB(0xFF9A2E), 1.0f);
    private static final int SPIRAL_TICKS = 40;
    private static final int RESPAWN_DELAY_TICKS = 2;

    private final CitadelleMessages plugin;

    Regeneration(CitadelleMessages plugin) {
        this.plugin = plugin;
    }

    private ConfigurationSection cfg() {
        ConfigurationSection s = plugin.getConfig().getConfigurationSection("regeneration");
        return s != null ? s : plugin.getConfig().createSection("regeneration");
    }

    @EventHandler(priority = EventPriority.HIGH)
    public void onDeath(PlayerDeathEvent event) {
        if (!cfg().getBoolean("enabled", true)) return;
        Player player = event.getEntity();
        Location loc = player.getLocation().add(0, 1, 0);
        World world = loc.getWorld();
        if (world != null) {
            world.spawnParticle(Particle.DUST, loc, 60, 0.35, 0.8, 0.35, 0, GOLD);
            world.spawnParticle(Particle.WAX_ON, loc, 30, 0.4, 0.8, 0.4, 0.5);
            world.spawnParticle(Particle.END_ROD, loc, 15, 0.2, 0.5, 0.2, 0.08);
            world.playSound(loc, Sound.BLOCK_BEACON_DEACTIVATE, 1.0f, 1.4f);
        }
        String prefix = cfg().getString("death-prefix", "");
        if (prefix != null && !prefix.isEmpty()) prefixDeathMessage(event, CitadelleMessages.colour(prefix));
    }

    @EventHandler(priority = EventPriority.MONITOR)
    public void onRespawn(PlayerRespawnEvent event) {
        if (!cfg().getBoolean("enabled", true)) return;
        Player player = event.getPlayer();
        plugin.getServer().getScheduler().runTaskLater(plugin, () -> regenerate(player), RESPAWN_DELAY_TICKS);
    }

    private void regenerate(Player player) {
        if (!player.isOnline() || player.isDead()) return;
        ConfigurationSection c = cfg();
        player.sendTitle(CitadelleMessages.colour(c.getString("title", "&6&l✦ Régénération ✦")),
                CitadelleMessages.colour(c.getString("subtitle", "&eUne nouvelle incarnation commence…")),
                10, 50, 20);
        player.playSound(player.getLocation(), Sound.BLOCK_BEACON_ACTIVATE, 1.0f, 1.2f);
        player.playSound(player.getLocation(), Sound.BLOCK_AMETHYST_BLOCK_RESONATE, 1.0f, 0.8f);
        int seconds = c.getInt("regen-seconds", 5);
        if (seconds > 0) {
            player.addPotionEffect(new PotionEffect(PotionEffectType.REGENERATION, seconds * 20, 0, false, false, true));
        }
        new BukkitRunnable() {
            private int tick = 0;

            @Override
            public void run() {
                if (!player.isOnline() || player.isDead() || tick >= SPIRAL_TICKS) {
                    cancel();
                    return;
                }
                spiral(player, tick);
                tick++;
            }
        }.runTaskTimer(plugin, 0L, 1L);
    }

    /** two golden strands rising around the player, then a burst from head and hands. */
    private static void spiral(Player player, int tick) {
        Location base = player.getLocation();
        World world = base.getWorld();
        if (world == null) return;
        double h = 2.2 * tick / SPIRAL_TICKS;
        for (int strand = 0; strand < 2; strand++) {
            double a = tick * 0.45 + strand * Math.PI;
            Location p = base.clone().add(Math.cos(a) * 0.7, h, Math.sin(a) * 0.7);
            world.spawnParticle(Particle.DUST, p, 2, 0.02, 0.02, 0.02, 0, strand == 0 ? GOLD : AMBER);
            world.spawnParticle(Particle.WAX_ON, p, 1, 0, 0, 0, 0.3);
        }
        if (tick == SPIRAL_TICKS - 1) {
            Location head = base.clone().add(0, 1.8, 0);
            world.spawnParticle(Particle.END_ROD, head, 25, 0.25, 0.25, 0.25, 0.12);
            world.spawnParticle(Particle.DUST, head, 40, 0.6, 0.4, 0.6, 0, GOLD);
            world.playSound(head, Sound.ENTITY_PLAYER_LEVELUP, 0.6f, 1.6f);
        }
    }

    /**
     * Paper keeps the death message as an Adventure component (translated client side, so it stays in French).
     * We prepend the legacy prefix through reflection so the plugin still compiles against spigot-api.
     */
    private void prefixDeathMessage(PlayerDeathEvent event, String legacyPrefix) {
        try {
            ClassLoader cl = event.getClass().getClassLoader();
            Class<?> component = Class.forName("net.kyori.adventure.text.Component", true, cl);
            Class<?> textColor = Class.forName("net.kyori.adventure.text.format.TextColor", true, cl);
            Class<?> named = Class.forName("net.kyori.adventure.text.format.NamedTextColor", true, cl);
            Class<?> legacy = Class.forName("net.kyori.adventure.text.serializer.legacy.LegacyComponentSerializer", true, cl);

            Method getter = PlayerDeathEvent.class.getMethod("deathMessage");
            Object message = getter.invoke(event);
            if (message == null) return;

            Object serializer = legacy.getMethod("legacySection").invoke(null);
            Object prefix = null;
            for (Method m : legacy.getMethods()) {
                if (m.getName().equals("deserialize") && m.getParameterCount() == 1
                        && m.getParameterTypes()[0] == String.class) {
                    prefix = m.invoke(serializer, legacyPrefix);
                    break;
                }
            }
            if (prefix == null) return;
            Object gray = named.getField("GRAY").get(null);
            Object greyed = component.getMethod("colorIfAbsent", textColor).invoke(message, gray);
            Object full = component.getMethod("append", component).invoke(prefix, greyed);
            PlayerDeathEvent.class.getMethod("deathMessage", component).invoke(event, full);
        } catch (ReflectiveOperationException | RuntimeException e) {
            plugin.getLogger().fine("Message de mort non modifie : " + e);
        }
    }
}
