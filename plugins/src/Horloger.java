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
import org.bukkit.event.entity.EntitySpawnEvent;
import org.bukkit.event.Listener;
import org.bukkit.event.entity.EntityDamageEvent;
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

/**
 * The Horloger NPC: a non-persistent Mannequin respawned on startup and whenever its chunk loads,
 * so it can never be duplicated. Right-click opens the chronon exchange; it turns to face nearby players.
 */
final class Horloger implements Listener {

    static final String TAG = "citadelle_horloger";
    private static final Color NAVY = Color.fromRGB(0x1B2340);
    private static final double LOOK_RANGE = 8;
    private static final long LOOK_PERIOD = 10L;

    private final CitadelleMessages plugin;
    private final ChrononShop shop;
    private Mannequin npc;

    Horloger(CitadelleMessages plugin, ChrononShop shop) {
        this.plugin = plugin;
        this.shop = shop;
        Bukkit.getScheduler().runTaskLater(plugin, this::respawn, 40L);
        Bukkit.getScheduler().runTaskTimer(plugin, this::look, 60L, LOOK_PERIOD);
    }

    private Location saved() {
        ConfigurationSection s = plugin.getConfig().getConfigurationSection("chronons.pnj");
        if (s == null) return null;
        World w = Bukkit.getWorld(s.getString("world", "world"));
        if (w == null) return null;
        return new Location(w, s.getDouble("x"), s.getDouble("y"), s.getDouble("z"), (float) s.getDouble("yaw"), 0f);
    }

    void place(Location at) {
        plugin.getConfig().set("chronons.pnj.world", at.getWorld().getName());
        plugin.getConfig().set("chronons.pnj.x", at.getBlockX() + 0.5);
        plugin.getConfig().set("chronons.pnj.y", at.getY());
        plugin.getConfig().set("chronons.pnj.z", at.getBlockZ() + 0.5);
        plugin.getConfig().set("chronons.pnj.yaw", Math.round(at.getYaw() / 45f) * 45f);
        plugin.saveConfig();
        respawn();
    }

    void removeForGood() {
        despawn();
        plugin.getConfig().set("chronons.pnj", null);
        plugin.saveConfig();
    }

    void respawn() {
        despawn();
        Location at = saved();
        if (at == null) return;
        for (Entity e : at.getChunk().getEntities()) {
            if (e.getScoreboardTags().contains(TAG)) e.remove();
        }
        npc = at.getWorld().spawn(at, Mannequin.class, this::dress);
        if (!npc.isValid()) plugin.getLogger().warning("L'Horloger n'a pas pu apparaître (un plugin bloque son apparition).");
    }

    private void dress(Mannequin m) {
        m.setPersistent(false);
        m.addScoreboardTag(TAG);
        m.setCustomName("§d§l⌛ L'Horloger");
        m.setCustomNameVisible(true);
        describe(m, "§7Échange de chronons");
        safely(() -> m.setImmovable(true));
        m.setInvulnerable(true);
        m.setSilent(true);
        m.setRemoveWhenFarAway(false);
        safely(() -> {                         // equipment only: a Mannequin is not a Mob (no drop chances)
            EntityEquipment eq = m.getEquipment();
            if (eq == null) return;
            eq.setChestplate(armour(Material.LEATHER_CHESTPLATE));
            eq.setLeggings(armour(Material.LEATHER_LEGGINGS));
            eq.setBoots(armour(Material.LEATHER_BOOTS));
            eq.setItemInMainHand(new ItemStack(Material.CLOCK));
            eq.setItemInOffHand(new ItemStack(Material.SPYGLASS));
        });
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
            for (java.lang.reflect.Method d : legacyClass.getMethods()) {
                if (d.getName().equals("deserialize") && d.getParameterCount() == 1 && d.getParameterTypes()[0] == String.class) {
                    text = d.invoke(serializer, legacy);
                    break;
                }
            }
            if (text == null) return;
            for (java.lang.reflect.Method set : Mannequin.class.getMethods()) {
                String n = set.getName().toLowerCase(java.util.Locale.ROOT);
                if (n.contains("description") && !n.contains("hide") && set.getParameterCount() == 1
                        && set.getParameterTypes()[0].isAssignableFrom(component)) {
                    set.invoke(m, text);
                    return;
                }
            }
            plugin.getLogger().info("Description du mannequin non supportée : nom seul affiché.");
        } catch (ReflectiveOperationException | RuntimeException e) {
            plugin.getLogger().fine("Description du mannequin impossible : " + e);
        }
    }

    private static ItemStack armour(Material type) {
        ItemStack it = new ItemStack(type);
        if (it.getItemMeta() instanceof LeatherArmorMeta meta) {
            meta.setColor(NAVY);
            if (meta instanceof ArmorMeta am) am.setTrim(new ArmorTrim(TrimMaterial.GOLD, TrimPattern.COAST));
            it.setItemMeta(meta);
        }
        return it;
    }

    void despawn() {
        if (npc != null && npc.isValid()) npc.remove();
        npc = null;
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
        float yaw = (float) Math.toDegrees(Math.atan2(-dx, dz));
        float pitch = (float) -Math.toDegrees(Math.atan2(dy, Math.sqrt(dx * dx + dz * dz)));
        npc.setRotation(yaw, pitch);
    }

    /**
     * The spawn's WorldGuard region denies mob spawning, which also cancels our Mannequin.
     * Only the Horloger (already tagged when the event fires) is let through.
     */
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

    private boolean isNpc(Entity e) {
        return e.getScoreboardTags().contains(TAG);
    }

    @EventHandler
    public void onInteract(PlayerInteractEntityEvent event) {
        if (!isNpc(event.getRightClicked())) return;
        event.setCancelled(true);
        if (event.getHand() == EquipmentSlot.HAND) shop.open(event.getPlayer());
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
