package fr.citadelle.messages;

import org.bukkit.Material;
import org.bukkit.NamespacedKey;
import org.bukkit.Registry;
import org.bukkit.enchantments.Enchantment;
import org.bukkit.inventory.ItemStack;
import org.bukkit.inventory.meta.EnchantmentStorageMeta;
import org.bukkit.inventory.meta.ItemMeta;

import java.util.List;
import java.util.Locale;
import java.util.Random;

/** Legendary "reliques temporelles" and enchanted books for the rift loot. */
final class RiftRelics {

    private record Relic(Material material, String name, List<String> lore, String[] enchants) { }

    private static final List<Relic> RELICS = List.of(
            new Relic(Material.NETHERITE_SWORD, "§6§l⚔ Lame du Gardien",
                    List.of("§7Forgée dans le cœur d'une faille,", "§7elle tranche jusqu'au fil du temps."),
                    new String[]{"sharpness:5", "unbreaking:3", "looting:3", "fire_aspect:2", "mending:1"}),
            new Relic(Material.BOW, "§b§l➹ Arc de la Sentinelle",
                    List.of("§7Ses flèches arrivent avant", "§7même d'avoir été tirées."),
                    new String[]{"power:5", "punch:2", "flame:1", "infinity:1", "unbreaking:3"}),
            new Relic(Material.NETHERITE_HELMET, "§5§l♛ Couronne du Seigneur du Temps",
                    List.of("§7Ceux qui la portent voient", "§7les secondes s'écouler au ralenti."),
                    new String[]{"protection:4", "unbreaking:3", "respiration:3", "aqua_affinity:1", "mending:1"}),
            new Relic(Material.NETHERITE_CHESTPLATE, "§5§l✦ Plastron de la Citadelle",
                    List.of("§7Le laiton de la Citadelle,", "§7trempé dans l'éternité."),
                    new String[]{"protection:4", "unbreaking:3", "mending:1"}),
            new Relic(Material.DIAMOND_BOOTS, "§e§l✧ Bottes du Voyageur temporel",
                    List.of("§7Pour marcher entre les époques", "§7sans jamais tomber."),
                    new String[]{"feather_falling:4", "depth_strider:3", "protection:4", "unbreaking:3"}),
            new Relic(Material.NETHERITE_PICKAXE, "§3§l⛏ Pioche des Âges",
                    List.of("§7Elle creuse à travers", "§7des millénaires de roche."),
                    new String[]{"efficiency:5", "fortune:3", "unbreaking:3", "mending:1"}));

    private RiftRelics() { }

    static ItemStack randomRelic(Random rnd) {
        Relic r = RELICS.get(rnd.nextInt(RELICS.size()));
        ItemStack item = new ItemStack(r.material());
        ItemMeta meta = item.getItemMeta();
        if (meta == null) return item;
        meta.setItemName(r.name());
        List<String> lore = new java.util.ArrayList<>(r.lore());
        lore.add("");
        lore.add("§8Relique temporelle");
        meta.setLore(lore);
        for (String e : r.enchants()) {
            String[] p = e.split(":");
            Enchantment ench = enchantment(p[0]);
            if (ench != null) meta.addEnchant(ench, Integer.parseInt(p[1]), true);
        }
        item.setItemMeta(meta);
        return item;
    }

    /** "mending" / "sharpness" + level, null when the enchantment does not exist. */
    static ItemStack book(String key, int level) {
        Enchantment ench = enchantment(key);
        if (ench == null) return null;
        ItemStack book = new ItemStack(Material.ENCHANTED_BOOK);
        if (book.getItemMeta() instanceof EnchantmentStorageMeta meta) {
            meta.addStoredEnchant(ench, Math.max(1, Math.min(level, ench.getMaxLevel())), true);
            book.setItemMeta(meta);
        }
        return book;
    }

    static Enchantment enchantment(String key) {
        return Registry.ENCHANTMENT.get(NamespacedKey.minecraft(key.toLowerCase(Locale.ROOT)));
    }
}
