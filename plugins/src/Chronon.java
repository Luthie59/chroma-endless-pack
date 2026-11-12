package fr.citadelle.messages;

import org.bukkit.Material;
import org.bukkit.NamespacedKey;
import org.bukkit.entity.Player;
import org.bukkit.inventory.ItemStack;
import org.bukkit.inventory.PlayerInventory;
import org.bukkit.inventory.meta.ItemMeta;
import org.bukkit.persistence.PersistentDataType;
import org.bukkit.plugin.Plugin;

import java.util.List;

/** The "Fragment de chronon" currency: creation, recognition, counting and spending. */
final class Chronon {

    private final NamespacedKey key;

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
