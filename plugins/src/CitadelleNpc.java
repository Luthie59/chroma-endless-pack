package fr.citadelle.messages;

import org.bukkit.Bukkit;
import org.bukkit.Color;
import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.World;
import org.bukkit.configuration.ConfigurationSection;
import org.bukkit.entity.Entity;
import org.bukkit.entity.Mannequin;
import org.bukkit.entity.Player;
import org.bukkit.event.EventHandler;
import org.bukkit.event.EventPriority;
import org.bukkit.event.Listener;
import org.bukkit.event.entity.EntityDamageEvent;
import org.bukkit.event.entity.EntitySpawnEvent;
import org.bukkit.event.player.PlayerInteractAtEntityEvent;
import org.bukkit.event.player.PlayerInteractEntityEvent;
import org.bukkit.event.world.ChunkLoadEvent;
import org.bukkit.inventory.EntityEquipment;
import org.bukkit.inventory.EquipmentSlot;
import org.bukkit.inventory.ItemStack;
import org.bukkit.inventory.meta.ArmorMeta;
import org.bukkit.inventory.meta.LeatherArmorMeta;
import org.bukkit.inventory.meta.trim.ArmorTrim;
import org.bukkit.inventory.meta.trim.TrimMaterial;
import org.bukkit.inventory.meta.trim.TrimPattern;

import java.lang.reflect.Method;
import java.util.Locale;
import java.util.function.Consumer;

/**
 * A Citadelle NPC (L'Horloger, L'Archiviste…): a non-persistent Mannequin respawned on startup and whenever
 * its chunk loads, so it can never be duplicated. Right-click runs {@code onClick}; it faces nearby players.
 */
final class CitadelleNpc implements Listener {

    /** what the NPC looks like and does. */
    record Spec(String configPath, String tag, String name, String description, Color outfit,
                Material mainHand, Material offHand, Consumer<Player> onClick) { }

    private static final double LOOK_RANGE = 8;
    private static final long LOOK_PERIOD = 10L;
    private static final long WATCHDOG_PERIOD = 100L;

    private final CitadelleMessages plugin;
    private final Spec spec;
    private Mannequin npc;

    CitadelleNpc(CitadelleMessages plugin, Spec spec) {
        this.plugin = plugin;
        this.spec = spec;
        Bukkit.getScheduler().runTaskLater(plugin, this::respawn, 40L);
        Bukkit.getScheduler().runTaskTimer(plugin, this::look, 60L, LOOK_PERIOD);
        Bukkit.getScheduler().runTaskTimer(plugin, this::watchdog, 100L, WATCHDOG_PERIOD);
    }

    private Location saved() {
        ConfigurationSection s = plugin.getConfig().getConfigurationSection(spec.configPath());
        if (s == null) return null;
        World w = Bukkit.getWorld(s.getString("world", "world"));
        if (w == null) return null;
        return new Location(w, s.getDouble("x"), s.getDouble("y"), s.getDouble("z"), (float) s.getDouble("yaw"), 0f);
    }

    void place(Location at) {
        String p = spec.configPath();
        plugin.getConfig().set(p + ".world", at.getWorld().getName());
        plugin.getConfig().set(p + ".x", at.getBlockX() + 0.5);
        plugin.getConfig().set(p + ".y", at.getY());
        plugin.getConfig().set(p + ".z", at.getBlockZ() + 0.5);
        plugin.getConfig().set(p + ".yaw", Math.round(at.getYaw() / 45f) * 45f);
        plugin.saveConfig();
        respawn();
    }

    void removeForGood() {
        despawn();
        plugin.getConfig().set(spec.configPath(), null);
        plugin.saveConfig();
    }

    void respawn() {
        despawn();
        Location at = saved();
        if (at == null) return;
        for (Entity e : at.getChunk().getEntities()) {
            if (e.getScoreboardTags().contains(spec.tag())) e.remove();
        }
        npc = at.getWorld().spawn(at, Mannequin.class, this::dress);
        if (!npc.isValid()) plugin.getLogger().warning(spec.name() + " n'a pas pu apparaître (un plugin bloque son apparition).");
    }

    void despawn() {
        if (npc != null && npc.isValid()) npc.remove();
        npc = null;
    }

    private void dress(Mannequin m) {
        m.setPersistent(false);
        m.addScoreboardTag(spec.tag());
        m.setCustomName(spec.name());
        m.setCustomNameVisible(true);
        describe(m, spec.description());
        safely(() -> m.setImmovable(true));
        m.setInvulnerable(true);
        m.setSilent(true);
        m.setRemoveWhenFarAway(false);
        safely(() -> {                         // equipment only: a Mannequin is not a Mob (no drop chances)
            EntityEquipment eq = m.getEquipment();
            if (eq == null) return;
            eq.setChestplate(armour(Material.LEATHER_CHESTPLATE, spec.outfit()));
            eq.setLeggings(armour(Material.LEATHER_LEGGINGS, spec.outfit()));
            eq.setBoots(armour(Material.LEATHER_BOOTS, spec.outfit()));
            if (spec.mainHand() != null) eq.setItemInMainHand(new ItemStack(spec.mainHand()));
            if (spec.offHand() != null) eq.setItemInOffHand(new ItemStack(spec.offHand()));
        });
    }

    private static ItemStack armour(Material type, Color colour) {
        ItemStack it = new ItemStack(type);
        if (it.getItemMeta() instanceof LeatherArmorMeta meta) {
            meta.setColor(colour);
            if (meta instanceof ArmorMeta am) am.setTrim(new ArmorTrim(TrimMaterial.GOLD, TrimPattern.COAST));
            it.setItemMeta(meta);
        }
        return it;
    }

    /** Mannequin-only API differs between Spigot and Paper: never let it break the NPC. */
    private void safely(Runnable call) {
        try {
            call.run();
        } catch (LinkageError | RuntimeException e) {
            plugin.getLogger().warning("Mannequin : " + e);
        }
    }

    /** Spigot: setDescription(String); Paper: a description setter taking an Adventure Component. */
    private void describe(Mannequin m, String legacy) {
        try {
            m.setDescription(legacy);
            return;
        } catch (LinkageError ignored) {
            // Paper server: fall through to the Component variant
        }
        try {
            ClassLoader cl = m.getClass().getClassLoader();
            Class<?> component = Class.forName("net.kyori.adventure.text.Component", true, cl);
            Class<?> legacyClass = Class.forName("net.kyori.adventure.text.serializer.legacy.LegacyComponentSerializer", true, cl);
            Object serializer = legacyClass.getMethod("legacySection").invoke(null);
            Object text = null;
            for (Method d : legacyClass.getMethods()) {
                if (d.getName().equals("deserialize") && d.getParameterCount() == 1 && d.getParameterTypes()[0] == String.class) {
                    text = d.invoke(serializer, legacy);
                    break;
                }
            }
            if (text == null) return;
            for (Method set : Mannequin.class.getMethods()) {
                String n = set.getName().toLowerCase(Locale.ROOT);
                if (n.contains("description") && !n.contains("hide") && set.getParameterCount() == 1
                        && set.getParameterTypes()[0].isAssignableFrom(component)) {
                    set.invoke(m, text);
                    return;
                }
            }
        } catch (ReflectiveOperationException | RuntimeException e) {
            plugin.getLogger().fine("Description du mannequin impossible : " + e);
        }
    }

    /** every few seconds: if our chunk is loaded but the entity is gone (chunk reloaded early, removed…), respawn. */
    private void watchdog() {
        Location at = saved();
        if (at == null || (npc != null && npc.isValid())) return;
        if (at.getWorld().isChunkLoaded(at.getBlockX() >> 4, at.getBlockZ() >> 4)) respawn();
    }

    /** turn toward the closest player. */
    private void look() {
        if (npc == null || !npc.isValid()) return;
        Location from = npc.getLocation();
        Player closest = null;
        double best = LOOK_RANGE * LOOK_RANGE;
        for (Player p : from.getWorld().getPlayers()) {
            double d = p.getLocation().distanceSquared(from);
            if (d < best) { best = d; closest = p; }
        }
        if (closest == null) return;
        double dx = closest.getLocation().getX() - from.getX(), dz = closest.getLocation().getZ() - from.getZ();
        double dy = closest.getEyeLocation().getY() - (from.getY() + 1.62);
        npc.setRotation((float) Math.toDegrees(Math.atan2(-dx, dz)), (float) -Math.toDegrees(Math.atan2(dy, Math.sqrt(dx * dx + dz * dz))));
    }

    private boolean isNpc(Entity e) {
        return e.getScoreboardTags().contains(spec.tag());
    }

    /** The spawn's WorldGuard region denies mob spawning, which also cancels the Mannequin: let ours through. */
    @EventHandler(priority = EventPriority.MONITOR)
    public void onSpawn(EntitySpawnEvent event) {
        if (event.isCancelled() && isNpc(event.getEntity())) event.setCancelled(false);
    }

    @EventHandler
    public void onChunkLoad(ChunkLoadEvent event) {
        Location at = saved();
        if (at == null || (npc != null && npc.isValid())) return;
        if (event.getWorld().equals(at.getWorld()) && event.getChunk().getX() == at.getBlockX() >> 4
                && event.getChunk().getZ() == at.getBlockZ() >> 4) {
            Bukkit.getScheduler().runTask(plugin, () -> { if (npc == null || !npc.isValid()) respawn(); });
        }
    }

    @EventHandler
    public void onInteract(PlayerInteractEntityEvent event) {
        if (!isNpc(event.getRightClicked())) return;
        event.setCancelled(true);
        if (event.getHand() == EquipmentSlot.HAND) spec.onClick().accept(event.getPlayer());
    }

    @EventHandler
    public void onInteractAt(PlayerInteractAtEntityEvent event) {
        if (isNpc(event.getRightClicked())) event.setCancelled(true);
    }

    @EventHandler
    public void onDamage(EntityDamageEvent event) {
        if (isNpc(event.getEntity())) event.setCancelled(true);
    }
}
