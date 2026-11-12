package fr.citadelle.messages;

import org.bukkit.Material;
import org.bukkit.NamespacedKey;
import org.bukkit.entity.Player;
import org.bukkit.event.EventHandler;
import org.bukkit.event.Listener;
import org.bukkit.event.player.PlayerJoinEvent;
import org.bukkit.inventory.Inventory;
import org.bukkit.inventory.ItemStack;
import org.bukkit.inventory.PlayerInventory;
import org.bukkit.inventory.meta.ItemMeta;
import org.bukkit.persistence.PersistentDataType;
import org.bukkit.plugin.Plugin;

import java.util.List;

/** The "Fragment de chronon" currency: creation, recognition, counting and spending. */
final class Chronon implements Listener {

    private final NamespacedKey key;
    private final NamespacedKey model = new NamespacedKey("chroma", "chronon");

    Chronon(Plugin plugin) {
        this.key = new NamespacedKey(plugin, "chronon");
    }

    ItemStack fragment(int amount) {
        ItemStack item = new ItemStack(Material.AMETHYST_SHARD, Math.max(1, amount));
        ItemMeta meta = item.getItemMeta();
        if (meta != null) {
            meta.setItemName("§d✦ Fragment de chronon");
            meta.setLore(List.of("§7Un éclat de temps figé,", "§7arraché à une faille temporelle.", "",
                    "§8À échanger auprès de l'Horloger (/chronon)"));
            meta.setEnchantmentGlintOverride(true);
            meta.setItemModel(model);
            meta.getPersistentDataContainer().set(key, PersistentDataType.BYTE, (byte) 1);
            item.setItemMeta(meta);
        }
        return item;
    }

    boolean isFragment(ItemStack item) {
        if (item == null || item.getType() != Material.AMETHYST_SHARD || !item.hasItemMeta()) return false;
        ItemMeta meta = item.getItemMeta();
        return meta != null && meta.getPersistentDataContainer().has(key, PersistentDataType.BYTE);
    }

    /** gives fragments made by older versions the current look (texture, lore) so they stack with new ones. */
    void refresh(Inventory inv) {
        ItemMeta current = fragment(1).getItemMeta();
        ItemStack[] contents = inv.getContents();
        boolean changed = false;
        for (ItemStack it : contents) {
            if (!isFragment(it) || current == null || current.equals(it.getItemMeta())) continue;
            it.setItemMeta(current.clone());
            changed = true;
        }
        if (changed) inv.setContents(contents);
    }

    @EventHandler
    public void onJoin(PlayerJoinEvent event) {
        refresh(event.getPlayer().getInventory());
        refresh(event.getPlayer().getEnderChest());
    }

    int count(Player p) {
        int n = 0;
        for (ItemStack it : p.getInventory().getStorageContents()) {
            if (isFragment(it)) n += it.getAmount();
        }
        return n;
    }

    /** removes {@code amount} fragments; false (and nothing removed) when the player has fewer. */
    boolean take(Player p, int amount) {
        if (count(p) < amount) return false;
        PlayerInventory inv = p.getInventory();
        ItemStack[] contents = inv.getStorageContents();
        int left = amount;
        for (int i = 0; i < contents.length && left > 0; i++) {
            ItemStack it = contents[i];
            if (!isFragment(it)) continue;
            int used = Math.min(left, it.getAmount());
            left -= used;
            if (used == it.getAmount()) contents[i] = null;
            else it.setAmount(it.getAmount() - used);
        }
        inv.setStorageContents(contents);
        return true;
    }
}
