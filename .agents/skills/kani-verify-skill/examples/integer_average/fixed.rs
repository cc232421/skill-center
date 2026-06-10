fn integer_average(a: i32, b: i32) -> i32 {
    a / 2 + b / 2 + (a % 2 + b % 2) / 2
}

fn main() {
    let a = 4;
    let b = 8;
    let result = integer_average(a, b);
    println!("The average of {} and {} is {}", a, b, result);
}
