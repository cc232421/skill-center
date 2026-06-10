fn lowest_unset_bit_ori(x: u32) -> Option<u8> {
    let mut mask = 1;
    for i in 0..32 {
        if x & mask == 0 {
            return Some(i);
        }
        mask <<= 1;
    }
    None
}

fn lowest_unset_bit_opt(x: u32) -> Option<u8> {
    if x == std::u32::MAX {
        return None;
    }
    let y = !x;
    Some(y.trailing_zeros() as u8)
}

fn main() {
    let x = 42;
    println!("Original: {:?}", lowest_unset_bit_ori(x));
    println!("Optimized: {:?}", lowest_unset_bit_opt(x));
}
