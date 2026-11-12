package fr.citadelle.messages;

import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.block.Block;
import org.bukkit.block.data.Ageable;
import org.bukkit.enchantments.Enchantment;
import org.bukkit.entity.Player;
import org.bukkit.event.EventHandler;
import org.bukkit.event.EventPriority;
import org.bukkit.event.Listener;
import org.bukkit.event.block.BlockBreakEvent;
import org.bukkit.event.block.BlockPlaceEvent;
import org.bukkit.event.entity.EntityDeathEvent;
import org.bukkit.event.entity.PlayerDeathEvent;
import org.bukkit.event.player.PlayerFishEvent;
import org.bukkit.event.player.PlayerQuitEvent;
import org.bukkit.inventory.ItemStack;

import java.util.HashSet;
import java.util.Set;

/** Feeds the quest book from gameplay events (kills, mining, harvest, fishing). */
final class QuestListener implements Listener {

    private static final int PLACED_MEMORY = 20_000;

    private final QuestBook book;
    /** blocks placed by players since startup: mining them again never counts (anti place/break farming). */
    private final Set<Location> placed = new HashSet<>();

    QuestListener(QuestBook book) {
        this.book = book;
    }

    @EventHandler(priority = EventPriority.MONITOR, ignoreCancelled = true)
    public void onPlace(BlockPlaceEvent event) {
        if (placed.size() >= PLACED_MEMORY) placed.clear();
        placed.add(event.getBlockPlaced().getLocation());
    }

    @EventHandler(priority = EventPriority.MONITOR, ignoreCancelled = true)
    public void onBreak(BlockBreakEvent event) {
        Player p = event.getPlayer();
        Block b = event.getBlock();
        Material m = b.getType();
        if (placed.remove(b.getLocation())) return;
        if (b.getBlockData() instanceof Ageable age && age.getAge() >= age.getMaximumAge()
                && m != Material.SUGAR_CANE && m != Material.CACTUS && m != Material.KELP && m != Material.BAMBOO) {
            book.advance(p, Quest.Type.RECOLTER, q -> q.matchesBlock(m), 1);
            return;
        }
        if (m.name().endsWith("_ORE") && silkTouch(p.getInventory().getItemInMainHand())) return;
        book.advance(p, Quest.Type.MINER, q -> q.matchesBlock(m), 1);
    }

    private static boolean silkTouch(ItemStack tool) {
        return tool != null && tool.containsEnchantment(Enchantment.SILK_TOUCH);
    }

    @EventHandler(priority = EventPriority.MONITOR)
    public void onKill(EntityDeathEvent event) {
        Player killer = event.getEntity().getKiller();
        if (killer == null || event.getEntity() instanceof Player) return;
        book.advance(killer, Quest.Type.TUER, q -> q.matchesEntity(event.getEntity()), 1);
    }

    @EventHandler(priority = EventPriority.MONITOR)
    public void onPlayerKill(PlayerDeathEvent event) {
        Player killer = event.getEntity().getKiller();
        if (killer == null || killer.equals(event.getEntity())) return;
        book.advance(killer, Quest.Type.TUER_JOUEUR, q -> true, 1);
    }

    @EventHandler(priority = EventPriority.MONITOR, ignoreCancelled = true)
    public void onFish(PlayerFishEvent event) {
        if (event.getState() == PlayerFishEvent.State.CAUGHT_FISH) book.advance(event.getPlayer(), Quest.Type.PECHER, q -> true, 1);
    }

    /** called by the time rift for each player who really fought in it. */
    void riftResult(Player p, boolean won) {
        book.advance(p, Quest.Type.FAILLE_PARTICIPER, q -> true, 1);
        if (won) book.advance(p, Quest.Type.FAILLE_GAGNER, q -> true, 1);
    }

    @EventHandler
    public void onQuit(PlayerQuitEvent event) {
        book.save();
    }
}
