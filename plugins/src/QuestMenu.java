package fr.citadelle.messages;

import org.bukkit.Bukkit;
import org.bukkit.Material;
import org.bukkit.Sound;
import org.bukkit.entity.Player;
import org.bukkit.event.EventHandler;
import org.bukkit.event.Listener;
import org.bukkit.event.inventory.InventoryClickEvent;
import org.bukkit.event.inventory.InventoryDragEvent;
import org.bukkit.inventory.Inventory;
import org.bukkit.inventory.InventoryHolder;
import org.bukkit.inventory.ItemFlag;
import org.bukkit.inventory.ItemStack;
import org.bukkit.inventory.meta.ItemMeta;

import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

/**
 * The Archiviste's register (Console background): daily quests on sockets 11-15 (header 10, bonus 16),
 * weekly quests on 30 and 32 (header 28, bonus 34), player summary on 4, close on 40.
 */
final class QuestMenu implements Listener {

    private static final class Holder implements InventoryHolder {
        private Inventory inventory;
        @Override public Inventory getInventory() { return inventory; }
    }

    // §r + 3 normal spaces (12 px) + 2 bold spaces (10 px) centre the 70 px bold title
    private static final String TITLE = "§f§r   §6§l  L'Archiviste";
    private static final int[] DAILY_SLOTS = {11, 12, 13, 14, 15};
    private static final int[] WEEKLY_SLOTS = {30, 32};
    private static final int SIZE = 45, INFO = 4, DAY_HEAD = 10, DAY_BONUS = 16, WEEK_HEAD = 28, WEEK_BONUS = 34, CLOSE = 40;
    private static final int BAR = 10;

    private final QuestBook book;
    private final Chronon chronon;

    QuestMenu(QuestBook book, Chronon chronon) {
        this.book = book;
        this.chronon = chronon;
    }

    void open(Player p) {
        Holder h = new Holder();
        Inventory inv = Bukkit.createInventory(h, SIZE, TITLE);
        h.inventory = inv;
        render(p, inv);
        p.openInventory(inv);
        p.playSound(p.getLocation(), Sound.ITEM_BOOK_PAGE_TURN, 1f, 0.9f);
    }

    private void render(Player p, Inventory inv) {
        UUID id = p.getUniqueId();
        inv.setItem(INFO, item(Material.WRITABLE_BOOK, "§6§l✎ Ton registre", List.of(
                "§7Quêtes accomplies : §e" + book.store().total(id),
                "§7Fragments en poche : §d" + chronon.count(p) + " ✦",
                "", "§8Les quêtes avancent toutes seules", "§8pendant que tu joues."), false));
        section(id, inv, Quest.Period.JOUR, DAILY_SLOTS, DAY_HEAD, DAY_BONUS, "§e§lQuêtes du jour", Material.CLOCK);
        section(id, inv, Quest.Period.SEMAINE, WEEKLY_SLOTS, WEEK_HEAD, WEEK_BONUS, "§d§lQuêtes de la semaine", Material.RECOVERY_COMPASS);
        inv.setItem(CLOSE, item(Material.BARRIER, "§c§lFermer", List.of(), false));
    }

    private void section(UUID id, Inventory inv, Quest.Period period, int[] slots, int head, int bonus, String title, Material headIcon) {
        inv.setItem(head, item(headIcon, title, List.of("§7Nouvelles quêtes dans §e" + fmt(book.untilReset(period)) + "§7.",
                "", "§8Chaque joueur reçoit les siennes."), false));
        List<Quest> quests = book.drawn(id, period);
        for (int i = 0; i < slots.length; i++) {
            inv.setItem(slots[i], i < quests.size() ? questItem(id, quests.get(i)) : null);
        }
        boolean all = !quests.isEmpty() && quests.stream().allMatch(q -> book.done(id, q));
        boolean got = book.bonusDone(id, period);
        inv.setItem(bonus, item(got ? Material.ENDER_CHEST : Material.CHEST,
                (got ? "§a✔ " : "§6") + "§lBonus " + (period == Quest.Period.JOUR ? "du jour" : "de la semaine"),
                List.of("§7Accomplis toutes les quêtes pour recevoir :",
                        QuestBook.rewardText(book.bonusChronons(period), book.bonusMoney(period)),
                        "", got ? "§aReçu !" : all ? "§eEn cours de remise…" : "§8Pas encore mérité."), got));
    }

    private ItemStack questItem(UUID id, Quest q) {
        boolean done = book.done(id, q);
        int v = done ? q.amount() : book.progress(id, q);
        int filled = (int) Math.round((double) v / q.amount() * BAR);
        String bar = "§a" + "▰".repeat(filled) + "§8" + "▱".repeat(BAR - filled);
        List<String> lore = new ArrayList<>();
        if (!q.objective().isEmpty()) lore.add("§7" + q.objective());
        lore.add(bar + " §f" + v + "§7/" + q.amount());
        lore.add("");
        lore.add("§7Récompense : " + QuestBook.rewardText(q.chronons(), q.money()));
        lore.add(done ? "§a✔ Accomplie" : "§8En cours…");
        return item(q.icon(), (done ? "§a✔ " : "§e") + q.name(), lore, done);
    }

    private static ItemStack item(Material m, String name, List<String> lore, boolean glint) {
        ItemStack it = new ItemStack(m);
        ItemMeta meta = it.getItemMeta();
        if (meta == null) return it;
        meta.setItemName(name);
        meta.setLore(lore);
        if (glint) meta.setEnchantmentGlintOverride(true);
        meta.addItemFlags(ItemFlag.HIDE_ATTRIBUTES, ItemFlag.HIDE_ADDITIONAL_TOOLTIP);
        it.setItemMeta(meta);
        return it;
    }

    private static String fmt(Duration d) {
        long h = d.toHours(), m = d.toMinutesPart();
        return h >= 24 ? (h / 24) + " j " + (h % 24) + " h" : h + " h " + String.format("%02d", m);
    }

    @EventHandler
    public void onClick(InventoryClickEvent event) {
        if (!(event.getView().getTopInventory().getHolder() instanceof Holder)) return;
        event.setCancelled(true);
        if (event.getRawSlot() == CLOSE && event.getWhoClicked() instanceof Player p) p.closeInventory();
    }

    @EventHandler
    public void onDrag(InventoryDragEvent event) {
        if (event.getView().getTopInventory().getHolder() instanceof Holder) event.setCancelled(true);
    }
}
