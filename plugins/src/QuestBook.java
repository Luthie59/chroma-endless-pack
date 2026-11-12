package fr.citadelle.messages;

import org.bukkit.Bukkit;
import org.bukkit.Sound;
import org.bukkit.configuration.ConfigurationSection;
import org.bukkit.entity.Player;

import java.lang.reflect.Method;
import java.time.DayOfWeek;
import java.time.Duration;
import java.time.LocalDate;
import java.time.ZoneId;
import java.time.ZonedDateTime;
import java.time.temporal.IsoFields;
import java.time.temporal.TemporalAdjusters;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;
import java.util.Random;
import java.util.UUID;

/**
 * The Archiviste's quest book: definitions, each player's personal draw for the day / week
 * (deterministic from uuid + period, so nothing to store), progress, completion rewards and bonuses.
 */
final class QuestBook {

    static final int MAX_DAILY = 5, MAX_WEEKLY = 2;

    private final CitadelleMessages plugin;
    private final Chronon chronon;
    private final QuestStore store;
    private List<Quest> daily = List.of(), weekly = List.of();
    private int dailyCount, weeklyCount, dailyBonusChronons, dailyBonusMoney, weeklyBonusChronons, weeklyBonusMoney;
    private ZoneId zone = ZoneId.of("Europe/Paris");
    private Method actionBar;

    QuestBook(CitadelleMessages plugin, Chronon chronon) {
        this.plugin = plugin;
        this.chronon = chronon;
        this.store = new QuestStore(plugin);
        try {
            actionBar = Player.class.getMethod("sendActionBar", String.class);   // Paper
        } catch (NoSuchMethodException e) {
            actionBar = null;
        }
        load();
        Bukkit.getScheduler().runTaskTimer(plugin, store::saveIfDirty, 1200L, 1200L);
    }

    void load() {
        ConfigurationSection s = plugin.getConfig().getConfigurationSection("archiviste");
        if (s == null) s = plugin.getConfig().createSection("archiviste");
        try {
            zone = ZoneId.of(s.getString("timezone", "Europe/Paris"));
        } catch (RuntimeException e) {
            zone = ZoneId.of("Europe/Paris");
        }
        dailyCount = Math.max(1, Math.min(MAX_DAILY, s.getInt("quotidiennes", MAX_DAILY)));
        weeklyCount = Math.max(1, Math.min(MAX_WEEKLY, s.getInt("hebdomadaires", MAX_WEEKLY)));
        dailyBonusChronons = s.getInt("bonus-jour.chronons", 5);
        dailyBonusMoney = s.getInt("bonus-jour.argent", 1000);
        weeklyBonusChronons = s.getInt("bonus-semaine.chronons", 25);
        weeklyBonusMoney = s.getInt("bonus-semaine.argent", 5000);
        List<Quest> d = new ArrayList<>(), w = new ArrayList<>();
        ConfigurationSection q = s.getConfigurationSection("quetes");
        if (q != null) {
            for (String id : q.getKeys(false)) {
                ConfigurationSection qs = q.getConfigurationSection(id);
                Quest quest = qs == null ? null : Quest.parse(id, qs, plugin.getLogger());
                if (quest == null) continue;
                (quest.period() == Quest.Period.JOUR ? d : w).add(quest);
            }
        }
        d.sort(Comparator.comparing(Quest::id));
        w.sort(Comparator.comparing(Quest::id));
        daily = List.copyOf(d);
        weekly = List.copyOf(w);
        if (daily.isEmpty()) plugin.getLogger().warning("Aucune quête quotidienne dans archiviste.quetes.");
    }

    void save() { store.saveIfDirty(); }

    QuestStore store() { return store; }

    // ------------------------------------------------------------------ periods & draws

    String periodId(Quest.Period p) {
        LocalDate today = LocalDate.now(zone);
        return p == Quest.Period.JOUR ? today.toString()
                : today.get(IsoFields.WEEK_BASED_YEAR) + "-W" + today.get(IsoFields.WEEK_OF_WEEK_BASED_YEAR);
    }

    Duration untilReset(Quest.Period p) {
        ZonedDateTime now = ZonedDateTime.now(zone);
        LocalDate next = p == Quest.Period.JOUR ? now.toLocalDate().plusDays(1)
                : now.toLocalDate().with(TemporalAdjusters.next(DayOfWeek.MONDAY));
        return Duration.between(now, next.atStartOfDay(zone));
    }

    /** the player's quests for the current period: a stable personal draw. */
    List<Quest> drawn(UUID id, Quest.Period p) {
        List<Quest> pool = new ArrayList<>(p == Quest.Period.JOUR ? daily : weekly);
        Collections.shuffle(pool, new Random(id.hashCode() * 31L + periodId(p).hashCode()));
        return List.copyOf(pool.subList(0, Math.min(pool.size(), p == Quest.Period.JOUR ? dailyCount : weeklyCount)));
    }

    int progress(UUID id, Quest q) { return store.progress(id, q, periodId(q.period())); }
    boolean done(UUID id, Quest q) { return store.done(id, q, periodId(q.period())); }
    boolean bonusDone(UUID id, Quest.Period p) { return store.bonus(id, p, periodId(p)); }
    int bonusChronons(Quest.Period p) { return p == Quest.Period.JOUR ? dailyBonusChronons : weeklyBonusChronons; }
    int bonusMoney(Quest.Period p) { return p == Quest.Period.JOUR ? dailyBonusMoney : weeklyBonusMoney; }

    // ------------------------------------------------------------------ progress

    /** adds progress to every active quest of the player accepted by {@code filter}. */
    void advance(Player p, Quest.Type type, java.util.function.Predicate<Quest> filter, int amount) {
        for (Quest.Period period : Quest.Period.values()) {
            for (Quest q : drawn(p.getUniqueId(), period)) {
                if (q.type() != type || !filter.test(q)) continue;
                String pid = periodId(period);
                if (store.done(p.getUniqueId(), q, pid)) continue;
                int v = store.add(p.getUniqueId(), q, pid, amount);
                if (v >= q.amount()) complete(p, q, pid);
                else bar(p, "§6✎ " + q.name() + " §8» §e" + v + "§7/" + q.amount());
            }
        }
    }

    private void complete(Player p, Quest q, String pid) {
        store.markDone(p.getUniqueId(), q, pid);
        reward(p, q.chronons(), q.money(), q.commands());
        p.sendTitle("§6§l✔ Quête accomplie", q.name(), 5, 50, 15);
        p.playSound(p.getLocation(), Sound.UI_TOAST_CHALLENGE_COMPLETE, 0.7f, 1.2f);
        p.sendMessage("§6✎ §7L'Archiviste note ta quête §e" + q.name() + "§7 : " + rewardText(q.chronons(), q.money()));
        List<Quest> all = drawn(p.getUniqueId(), q.period());
        if (all.stream().allMatch(x -> store.done(p.getUniqueId(), x, pid)) && !store.bonus(p.getUniqueId(), q.period(), pid)) {
            store.markBonus(p.getUniqueId(), q.period(), pid);
            int c = bonusChronons(q.period()), m = bonusMoney(q.period());
            reward(p, c, m, List.of());
            String what = q.period() == Quest.Period.JOUR ? "du jour" : "de la semaine";
            p.sendMessage("§6✦ §eToutes les quêtes " + what + " sont accomplies ! §7Bonus : " + rewardText(c, m));
            p.playSound(p.getLocation(), Sound.ENTITY_PLAYER_LEVELUP, 0.8f, 1f);
        }
    }

    private void reward(Player p, int chronons, int money, List<String> commands) {
        for (int left = chronons; left > 0; left -= 64) {
            p.getInventory().addItem(chronon.fragment(Math.min(64, left)))
                    .values().forEach(it -> p.getWorld().dropItemNaturally(p.getLocation(), it));
        }
        List<String> cmds = new ArrayList<>(commands);
        if (money > 0) cmds.add("eco give {player} " + money);
        for (String cmd : cmds) {
            String line = cmd.replace("{player}", p.getName());
            try {
                Bukkit.dispatchCommand(Bukkit.getConsoleSender(), line);
            } catch (RuntimeException e) {
                plugin.getLogger().warning("Récompense de quête échouée (" + line + ") : " + e);
            }
        }
    }

    static String rewardText(int chronons, int money) {
        List<String> parts = new ArrayList<>();
        if (chronons > 0) parts.add("§d" + chronons + " ✦ fragments");
        if (money > 0) parts.add("§e" + money + " $");
        return parts.isEmpty() ? "§7—" : String.join(" §7+ ", parts);
    }

    private void bar(Player p, String text) {
        if (actionBar == null) return;
        try {
            actionBar.invoke(p, text);
        } catch (ReflectiveOperationException | RuntimeException ignored) {
            actionBar = null;                     // stop trying on servers without it
        }
    }
}
