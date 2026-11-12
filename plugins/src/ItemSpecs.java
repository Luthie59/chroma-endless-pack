package fr.citadelle.messages;

import org.bukkit.Material;
import org.bukkit.inventory.ItemStack;

import java.util.Locale;
import java.util.Random;

/**
 * Item specifications shared by the rift loot and the chronon exchange:
 * "MATERIAL", "CHRONON", "RELIC" or "ENCHANTED_BOOK:key[:level]".
 */
final class ItemSpecs {

    private ItemSpecs() { }

    /** @return the item, or null when the spec is unknown. */
    static ItemStack create(String spec, int amount, Chronon chronon, Random rnd) {
        String id = spec.trim();
        String upper = id.toUpperCase(Locale.ROOT);
        if (upper.equals("CHRONON")) return chronon.fragment(amount);
        if (upper.equals("RELIC")) return RiftRelics.randomRelic(rnd);
        if (upper.startsWith("ENCHANTED_BOOK:")) {
            String[] b = id.split(":");
            try {
                return RiftRelics.book(b[1], b.length > 2 ? Integer.parseInt(b[2]) : 99);
            } catch (NumberFormatException e) {
                return null;
            }
        }
        Material m = Material.matchMaterial(id);
        if (m == null || !m.isItem() || m.isAir()) return null;
        return new ItemStack(m, Math.max(1, Math.min(amount, m.getMaxStackSize())));
    }
}
