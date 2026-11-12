package fr.citadelle.messages;

import org.bukkit.Bukkit;
import org.bukkit.Material;
import org.bukkit.Sound;
import org.bukkit.configuration.ConfigurationSection;
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

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Random;

/**
 * "L'Horloger": exchange chronon fragments for goods. Uses the Console temporelle background glyph
 * (sockets on slots 4, 10-16, 28, 30, 32, 34, 40) with a centred bold title.
 */
final class ChrononShop implements Listener {

    record Offer(int slot, int price, Material icon, String name, List<String> description,
                 List<String> gives, List<String> commands) { }

    /** marks our inventories so clicks can be recognised. */
    private static final class Holder implements InventoryHolder {
        private Inventory inventory;
        @Override public Inventory getInventory() { return inventory; }
    }

    private static final String TITLE = "§f§6§l     L'Horloger";   // 5 bold spaces centre the 63 px title
    private static final int INFO_SLOT = 4, CLOSE_SLOT = 40, SIZE = 45;

    private final CitadelleMessages plugin;
    private final Chronon chronon;
    private final Random rnd = new Random();
    private Map<Integer, Offer> offers = Map.of();

    ChrononShop(CitadelleMessages plugin, Chronon chronon) {
        this.plugin = plugin;
        this.chronon = chronon;
        load();
    }

    void load() {
        ConfigurationSection s = plugin.getConfig().getConfigurationSection("chronons.offres");
        Map<Integer, Offer> map = new java.util.TreeMap<>();
        if (s == null) {
            plugin.getLogger().warning("Section chronons.offres absente : l'Horloger n'a rien à proposer.");
        } else {
            for (String id : s.getKeys(false)) {
                ConfigurationSection o = s.getConfigurationSection(id);
                if (o == null) continue;
                Material icon = Material.matchMaterial(o.getString("icone", "PAPER"));
                int slot = o.getInt("slot", -1);
                if (slot < 0 || slot >= SIZE || slot == INFO_SLOT || slot == CLOSE_SLOT || icon == null) {
                    plugin.getLogger().warning("Offre de chronons invalide : " + id);
                    continue;
                }
                map.put(slot, new Offer(slot, Math.max(1, o.getInt("prix", 1)), icon,
                        CitadelleMessages.colour(o.getString("nom", id)),
                        o.getStringList("description").stream().map(CitadelleMessages::colour).toList(),
                        o.getStringList("donne"), o.getStringList("commandes")));
            }
        }
        offers = Map.copyOf(map);
    }

    void open(Player p) {
        Holder holder = new Holder();
        Inventory inv = Bukkit.createInventory(holder, SIZE, TITLE);
        holder.inventory = inv;
        render(p, inv);
        p.openInventory(inv);
        p.playSound(p.getLocation(), Sound.BLOCK_AMETHYST_BLOCK_CHIME, 0.8f, 1.2f);
    }

    private void render(Player p, Inventory inv) {
        int have = chronon.count(p);
        ItemStack info = chronon.fragment(1);
        ItemMeta im = info.getItemMeta();
        if (im != null) {
            im.setItemName("§d§l✦ Tes fragments : " + have);
            im.setLore(List.of("§7Les failles temporelles en regorgent :", "§7Gardien, échos du temps, coffre du temps.",
                    "", "§8Échange-les contre les trésors ci-dessous."));
            info.setItemMeta(im);
        }
        inv.setItem(INFO_SLOT, info);
        for (Offer o : offers.values()) inv.setItem(o.slot(), icon(o, have));
        ItemStack close = new ItemStack(Material.BARRIER);
        ItemMeta cm = close.getItemMeta();
        if (cm != null) { cm.setItemName("§c§lFermer"); close.setItemMeta(cm); }
        inv.setItem(CLOSE_SLOT, close);
    }

    private static ItemStack icon(Offer o, int have) {
        ItemStack it = new ItemStack(o.icon());
        ItemMeta meta = it.getItemMeta();
        if (meta == null) return it;
        meta.setItemName(o.name());
        List<String> lore = new ArrayList<>(o.description());
        lore.add("");
        lore.add("§7Prix : §d" + o.price() + " ✦ fragments");
        lore.add(have >= o.price() ? "§8» §eClic pour échanger" : "§c✖ Il te manque " + (o.price() - have) + " fragments");
        meta.setLore(lore);
        meta.addItemFlags(ItemFlag.HIDE_ATTRIBUTES, ItemFlag.HIDE_ADDITIONAL_TOOLTIP);
        it.setItemMeta(meta);
        return it;
    }

    @EventHandler
    public void onClick(InventoryClickEvent event) {
        if (!(event.getView().getTopInventory().getHolder() instanceof Holder)) return;
        event.setCancelled(true);
        if (!(event.getWhoClicked() instanceof Player p) || event.getClickedInventory() != event.getView().getTopInventory()) return;
        int slot = event.getRawSlot();
        if (slot == CLOSE_SLOT) { p.closeInventory(); return; }
        Offer o = offers.get(slot);
        if (o != null) buy(p, o, event.getView().getTopInventory());
    }

    @EventHandler
    public void onDrag(InventoryDragEvent event) {
        if (event.getView().getTopInventory().getHolder() instanceof Holder) event.setCancelled(true);
    }

    private void buy(Player p, Offer o, Inventory inv) {
        if (!chronon.take(p, o.price())) {
            p.sendMessage("§5⌛ §cIl te manque §d" + (o.price() - chronon.count(p)) + " fragments §cpour cet échange.");
            p.playSound(p.getLocation(), Sound.ENTITY_VILLAGER_NO, 0.8f, 1f);
            return;
        }
        for (String spec : o.gives()) {
            String[] parts = spec.trim().split("\\s+");
            int amount = 1;
            try {
                if (parts.length > 1) amount = Integer.parseInt(parts[1]);
            } catch (NumberFormatException ignored) {
                plugin.getLogger().warning("Quantité invalide dans l'offre " + o.name() + " : " + spec);
            }
            ItemStack item = ItemSpecs.create(parts[0], amount, chronon, rnd);
            if (item == null) {
                plugin.getLogger().warning("Objet inconnu dans l'offre " + o.name() + " : " + spec);
                continue;
            }
            p.getInventory().addItem(item).values().forEach(left -> p.getWorld().dropItemNaturally(p.getLocation(), left));
        }
        for (String cmd : o.commands()) {
            String line = cmd.replace("{player}", p.getName());
            try {
                Bukkit.dispatchCommand(Bukkit.getConsoleSender(), line);
            } catch (RuntimeException e) {
                plugin.getLogger().warning("Commande d'échange échouée (" + line + ") : " + e);
            }
        }
        p.sendMessage("§5⌛ §7Échange conclu : " + o.name() + " §7contre §d" + o.price() + " fragments§7.");
        p.playSound(p.getLocation(), Sound.ENTITY_VILLAGER_TRADE, 0.8f, 1f);
        p.playSound(p.getLocation(), Sound.BLOCK_AMETHYST_BLOCK_RESONATE, 0.8f, 1.4f);
        render(p, inv);
    }
}
