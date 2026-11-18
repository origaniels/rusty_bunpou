//! Pie chart geometry: SVG path data for each slice, so the UI only has to fill paths.

/// One slice: index of the category it represents and its SVG path (in a `size`×`size` box).
#[derive(Debug, Clone, PartialEq)]
pub struct Slice {
    pub category: usize,
    pub path: String,
}

/// Slices for `counts`, starting at 12 o'clock and going clockwise. Empty categories get no
/// slice; a single non-empty category is drawn as a full circle; an all-zero input gives nothing.
pub fn pie_slices(counts: &[u32], size: f32) -> Vec<Slice> {
    let total: u32 = counts.iter().sum();
    let r = size / 2.0;
    let (cx, cy) = (r, r);
    let nonzero = counts.iter().filter(|&&c| c > 0).count();
    if total == 0 {
        return vec![];
    }
    if nonzero == 1 {
        let category = counts.iter().position(|&c| c > 0).unwrap();
        // two half arcs: a single arc can't start and end at the same point
        let path = format!(
            "M {cx} {top} A {r} {r} 0 1 1 {cx} {bottom} A {r} {r} 0 1 1 {cx} {top} Z",
            top = cy - r,
            bottom = cy + r
        );
        return vec![Slice { category, path }];
    }
    let point = |frac: f64| {
        let a = frac * std::f64::consts::TAU - std::f64::consts::FRAC_PI_2;
        (cx as f64 + r as f64 * a.cos(), cy as f64 + r as f64 * a.sin())
    };
    let mut out = vec![];
    let mut acc = 0u32;
    for (category, &c) in counts.iter().enumerate() {
        if c == 0 {
            continue;
        }
        let start = acc as f64 / total as f64;
        acc += c;
        let end = acc as f64 / total as f64;
        let (x1, y1) = point(start);
        let (x2, y2) = point(end);
        let large = if end - start > 0.5 { 1 } else { 0 };
        let path = format!("M {cx} {cy} L {x1:.2} {y1:.2} A {r} {r} 0 {large} 1 {x2:.2} {y2:.2} Z");
        out.push(Slice { category, path });
    }
    out
}

#[cfg(test)]
mod tests {
    use super::*;

    fn nums(path: &str) -> Vec<f32> {
        path.split_whitespace().filter_map(|t| t.parse().ok()).collect()
    }

    #[test]
    fn empty_and_single() {
        assert!(pie_slices(&[0, 0, 0], 100.0).is_empty());
        let s = pie_slices(&[0, 7, 0], 100.0);
        assert_eq!(s.len(), 1);
        assert_eq!(s[0].category, 1);
        assert!(s[0].path.matches(" A ").count() == 2, "full circle = two arcs");
    }

    #[test]
    fn slices_cover_the_circle_in_order() {
        let s = pie_slices(&[1, 0, 1, 2], 100.0);
        assert_eq!(s.iter().map(|x| x.category).collect::<Vec<_>>(), [0, 2, 3]);
        // first slice starts at 12 o'clock
        let n = nums(&s[0].path);
        assert_eq!((n[0], n[1]), (50.0, 50.0));
        assert!((n[2] - 50.0).abs() < 0.01 && n[3].abs() < 0.01, "{:?}", n);
        // last slice ends back at 12 o'clock; the half-circle one is not a "large" arc
        let last = nums(&s[2].path);
        assert!((last[last.len() - 2] - 50.0).abs() < 0.01 && last[last.len() - 1].abs() < 0.01);
        assert!(s[2].path.contains(" 0 0 1 "), "exactly half: small arc flag");
        // every end point lies on the circle
        for sl in &s {
            let n = nums(&sl.path);
            let (x, y) = (n[n.len() - 2], n[n.len() - 1]);
            assert!(((x - 50.0).powi(2) + (y - 50.0).powi(2)).sqrt() - 50.0 < 0.05);
        }
    }

    #[test]
    fn large_arc_flag_for_big_slices() {
        let s = pie_slices(&[3, 1], 100.0);
        assert!(s[0].path.contains(" 0 1 1 "), "{}", s[0].path);
        assert!(s[1].path.contains(" 0 0 1 "), "{}", s[1].path);
    }
}
