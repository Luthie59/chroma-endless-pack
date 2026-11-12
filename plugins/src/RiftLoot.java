package fr.citadelle.messages;

import org.bukkit.Bukkit;
import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.Particle;
import org.bukkit.Tag;
import org.bukkit.World;
import org.bukkit.block.Block;
import org.bukkit.block.BlockFace;
import org.bukkit.block.Chest;
import org.bukkit.block.DoubleChest;
import org.bukkit.configuration.file.YamlConfiguration;
import org.bukkit.entity.Player;
import org.bukkit.event.EventHandler;
import org.bukkit.event.EventPriority;
import org.bukkit.event.Listener;
import org.bukkit.event.block.BlockBreakEvent;
import org.bukkit.event.block.BlockExplodeEvent;
import org.bukkit.event.block.BlockPistonExtendEvent;
import org.bukkit.event.block.BlockPistonRetractEvent;
import org.bukkit.event.block.BlockPlaceEvent;
import org.bukkit.event.entity.EntityExplodeEvent;
import org.bukkit.event.inventory.InventoryMoveItemEvent;
import org.bukkit.event.inventory.InventoryOpenEvent;
import org.bukkit.inventory.Inventory;
import org.bukkit.inventory.InventoryHolder;
import org.bukkit.inventory.ItemStack;
import org.bukkit.plugin.Plugin;
import org.bukkit.scheduler.BukkitTask;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Random;
import java.util.logging.Logger;

/**
 * "Coffre du temps": loot chest left by a won rift. Reserved to the winners for a while, and always
 * shielded from double-chest merging, hoppers, explosions and pistons. Its position is saved to disk so a
 * crash never leaves a forgotten loot chest in the world.
 */
final class RiftLoot implements Listener {

    private static final BlockFace[] SIDES = {BlockFace.NORTH, BlockFace.SOUTH, BlockFace.EAST, BlockFace.WEST};

    private final Plugin plugin;
    private final FactionBridge factions;
    private final Chronon chronon;
    private final Logger log;
    private final File store;
    private final Random rnd = new Random();

    private Block chest;
    private String ownerKey;
    private long protectedUntil;
    private BukkitTask expiry, sparkle;

    RiftLoot(Plugin plugin, FactionBridge factions, Chronon chronon) {
        this.plugin = plugin;
        this.factions = factions;
        this.chronon = chronon;
        this.log = plugin.getLogger();
        this.store = new File(plugin.getDataFolder(), "faille-coffre.yml");
        cleanLeftover();
    }

    /** @return true when the chest was actually placed. */
    boolean place(Location center, FactionBridge.Team winner, RiftConfig cfg) {
        remove();
        Block b = center.getBlock();
        for (int i = 0; i < 8 && !replaceable(b); i++) b = b.getRelative(BlockFace.UP);
        if (!replaceable(b)) {
            log.warning("Coffre du temps impossible à poser près de " + center.getBlockX() + " " + center.getBlockY() + " " + center.getBlockZ());
            return false;
        }
        b.setType(Material.CHEST);
        if (b.getState() instanceof Chest state) fill(state.getBlockInventory(), cfg.loot());
        chest = b;
        ownerKey = winner.key();
        protectedUntil = System.currentTimeMillis() + cfg.chestProtectionSeconds() * 1000L;
        save(b);
        Location fx = b.getLocation().add(0.5, 1.1, 0.5);
        sparkle = Bukkit.getScheduler().runTaskTimer(plugin, () ->
                fx.getWorld().spawnParticle(Particle.WAX_ON, fx, 6, 0.3, 0.3, 0.3, 0.2), 0L, 10L);
        expiry = Bukkit.getScheduler().runTaskLater(plugin, this::remove, cfg.chestLifetimeSeconds() * 20L);
        log.info("Coffre du temps posé en " + b.getX() + " " + b.getY() + " " + b.getZ());
        return true;
    }

    /** air, plants, snow layers and leaves can make room for the chest. */
    private static boolean replaceable(Block b) {
        return b.isPassable() || Tag.LEAVES.isTagged(b.getType());
    }

    private void fill(Inventory inv, List<String> lines) {
        List<Integer> slots = new ArrayList<>();
        for (int i = 0; i < inv.getSize(); i++) slots.add(i);
        Collections.shuffle(slots, rnd);
        int next = 0;
        for (String line : lines) {
            ItemStack item = parse(line);
            if (item == null || next >= slots.size()) continue;
            inv.setItem(slots.get(next++), item);
        }
    }

    /** "MATERIAL min-max chance%" ; CHRONON, RELIC and ENCHANTED_BOOK:key[:level] are special, null when the roll fails or the line is invalid. */
    private ItemStack parse(String line) {
        String[] p = line.trim().split("\\s+");
        if (p.length == 0 || p[0].isEmpty()) return null;
        try {
            int min = 1, max = 1;
            if (p.length > 1) {
                String[] r = p[1].split("-");
                min = Integer.parseInt(r[0]);
                max = r.length > 1 ? Integer.parseInt(r[1]) : min;
            }
            double chance = p.length > 2 ? Double.parseDouble(p[2]) / 100.0 : 1.0;
            if (rnd.nextDouble() >= chance) return null;
            int amount = min + rnd.nextInt(Math.max(1, max - min + 1));
            ItemStack item = ItemSpecs.create(p[0], amount, chronon, rnd);
            if (item == null) log.warning("Butin de faille invalide : " + line);
            return item;
        } catch (NumberFormatException e) {
            log.warning("Butin de faille invalide : " + line);
            return null;
        }
    }

    // ------------------------------------------------------------------ protection

    private boolean isChest(Block b) {
        return chest != null && chest.equals(b);
    }

    private boolean holds(InventoryHolder holder) {
        if (chest == null || holder == null) return false;
        if (holder instanceof DoubleChest dc) return holds(dc.getLeftSide()) || holds(dc.getRightSide());
        return holder instanceof Chest c && isChest(c.getBlock());
    }

    private boolean deniedFor(Player p) {
        if (chest == null || System.currentTimeMillis() >= protectedUntil) return false;
        if (p.hasPermission("citadelle.faille.admin")) return false;
        return !factions.teamOf(p).key().equals(ownerKey);
    }

    @EventHandler(priority = EventPriority.HIGH)
    public void onOpen(InventoryOpenEvent event) {
        if (!(event.getPlayer() instanceof Player p) || !holds(event.getInventory().getHolder())) return;
        if (deniedFor(p)) {
            event.setCancelled(true);
            long left = Math.max(1, (protectedUntil - System.currentTimeMillis()) / 1000);
            p.sendMessage("§5⌛ §7Le coffre du temps appartient aux vainqueurs encore §e" + left + " s§7.");
        }
    }

    @EventHandler(priority = EventPriority.HIGH)
    public void onBreak(BlockBreakEvent event) {
        if (isChest(event.getBlock()) && deniedFor(event.getPlayer())) event.setCancelled(true);
    }

    /** no chest / trapped chest next to it: it would merge into a double chest. */
    @EventHandler(priority = EventPriority.HIGH)
    public void onPlace(BlockPlaceEvent event) {
        if (chest == null) return;
        Material m = event.getBlockPlaced().getType();
        if (m != Material.CHEST && m != Material.TRAPPED_CHEST) return;
        for (BlockFace f : SIDES) {
            if (isChest(event.getBlockPlaced().getRelative(f))) { event.setCancelled(true); return; }
        }
    }

    @EventHandler(priority = EventPriority.HIGH)
    public void onHopper(InventoryMoveItemEvent event) {
        if (holds(event.getSource().getHolder()) || holds(event.getDestination().getHolder())) event.setCancelled(true);
    }

    @EventHandler(priority = EventPriority.HIGH)
    public void onEntityExplode(EntityExplodeEvent event) {
        if (chest != null) event.blockList().remove(chest);
    }

    @EventHandler(priority = EventPriority.HIGH)
    public void onBlockExplode(BlockExplodeEvent event) {
        if (chest != null) event.blockList().remove(chest);
    }

    @EventHandler(priority = EventPriority.HIGH)
    public void onPistonPush(BlockPistonExtendEvent event) {
        if (chest != null && event.getBlocks().contains(chest)) event.setCancelled(true);
    }

    @EventHandler(priority = EventPriority.HIGH)
    public void onPistonPull(BlockPistonRetractEvent event) {
        if (chest != null && event.getBlocks().contains(chest)) event.setCancelled(true);
    }

    // ------------------------------------------------------------------ cleanup

    void remove() {
        if (expiry != null) expiry.cancel();
        if (sparkle != null) sparkle.cancel();
        expiry = sparkle = null;
        if (chest != null) wipe(chest);
        chest = null;
        ownerKey = null;
        if (store.exists() && !store.delete()) log.warning("Impossible d'effacer " + store.getName());
    }

    private static void wipe(Block b) {
        if (b.getType() != Material.CHEST) return;
        if (b.getState() instanceof Chest state) state.getBlockInventory().clear();
        b.setType(Material.AIR);
    }

    private void save(Block b) {
        YamlConfiguration y = new YamlConfiguration();
        y.set("world", b.getWorld().getName());
        y.set("x", b.getX());
        y.set("y", b.getY());
        y.set("z", b.getZ());
        try {
            y.save(store);
        } catch (IOException e) {
            log.warning("Position du coffre du temps non sauvegardée : " + e.getMessage());
        }
    }

    /** a chest left behind by a crash is removed at startup. */
    private void cleanLeftover() {
        if (!store.exists()) return;
        YamlConfiguration y = YamlConfiguration.loadConfiguration(store);
        World w = Bukkit.getWorld(y.getString("world", "world"));
        if (w != null) {
            wipe(w.getBlockAt(y.getInt("x"), y.getInt("y"), y.getInt("z")));
            log.info("Ancien coffre du temps retiré.");
        }
        if (!store.delete()) log.warning("Impossible d'effacer " + store.getName());
    }
}
